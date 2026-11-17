"""AI Financial Assistant orchestration and deterministic tool executor (Phase 8)."""

from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.assistant import AIConversation, AIMessage
from app.schemas.assistant import ChatMessageRead, ChatRequest, ChatResponse
from app.services.assistant_tools import ASSISTANT_TOOL_DEFINITIONS, AssistantTools

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are FinSight AI, a trusted personal credit card and rewards financial intelligence assistant.

Core Principles:
1. NEVER do mental math or calculate financial numbers yourself. ALWAYS rely exclusively on the exact figures returned by the deterministic tools.
2. Format currency in Indian Rupees (e.g. ₹5,000.00).
3. When recommending a credit card, clearly state the winning card, effective reward %, net INR benefit, applied rule condition, and cap status.
4. Keep your responses structured, clear, and actionable. Use bullet points and bold highlights for critical financial figures."""


class AssistantService:
    """Orchestrates assistant conversations, tool invocations, and responses."""

    @classmethod
    async def chat(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        req: ChatRequest,
    ) -> ChatResponse:
        """Process user message, execute deterministic tools, and return assistant response."""
        settings = get_settings()

        # 1. Resolve or create conversation
        conversation: AIConversation | None = None
        if req.conversation_id:
            stmt = (
                select(AIConversation)
                .where(
                    AIConversation.id == req.conversation_id,
                    AIConversation.user_id == user_id,
                )
                .options(selectinload(AIConversation.messages))
            )
            conversation = (await db.execute(stmt)).scalar_one_or_none()

        if not conversation:
            # Generate title from first few words of prompt
            words = req.message.strip().split()
            title = " ".join(words[:5]) if words else "Financial Advisory Session"
            if len(title) > 60:
                title = title[:57] + "..."
            conversation = AIConversation(user_id=user_id, title=title)
            db.add(conversation)
            await db.flush()

        # 2. Record User Message
        user_msg = AIMessage(
            conversation_id=conversation.id,
            user_id=user_id,
            role="user",
            content=req.message,
        )
        db.add(user_msg)
        await db.flush()

        # 3. Handle Chat: LLM with tool calling or deterministic local offline engine
        executed_tools: list[dict[str, Any]] = []

        if settings.ai_enabled and settings.openai_api_key:
            reply_content, executed_tools = await cls._execute_llm_tool_loop(
                db, user_id, conversation, req.message
            )
        else:
            reply_content, executed_tools = await cls._execute_rule_based_advisory(
                db, user_id, req.message
            )

        # 4. Record Assistant Message
        assistant_msg = AIMessage(
            conversation_id=conversation.id,
            user_id=user_id,
            role="assistant",
            content=reply_content,
            tool_calls=executed_tools if executed_tools else None,
        )
        db.add(assistant_msg)
        await db.commit()
        await db.refresh(assistant_msg)

        return ChatResponse(
            conversation_id=conversation.id,
            message=ChatMessageRead.model_validate(assistant_msg),
            tool_calls_executed=executed_tools,
        )

    @classmethod
    async def _execute_tool(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        tool_name: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """Dispatch deterministic tool calls strictly scoped to user_id."""
        if tool_name == "get_card_summary":
            return await AssistantTools.get_card_summary(db, user_id)
        elif tool_name == "get_upcoming_dues":
            return await AssistantTools.get_upcoming_dues(db, user_id)
        elif tool_name == "get_spending_analytics":
            return await AssistantTools.get_spending_analytics(db, user_id)
        elif tool_name == "evaluate_purchase_rewards":
            return await AssistantTools.evaluate_purchase_rewards(
                db,
                user_id,
                amount=float(args.get("amount", 5000)),
                merchant=str(args.get("merchant", "")),
                category=str(args.get("category", "Shopping")),
                channel=str(args.get("channel", "online")),
            )
        elif tool_name == "get_cap_status":
            return await AssistantTools.get_cap_status(db, user_id)
        elif tool_name == "detect_missing_rewards":
            return await AssistantTools.detect_missing_rewards(db, user_id)
        elif tool_name == "search_transactions":
            return await AssistantTools.search_transactions(
                db, user_id, query=str(args.get("query", "")), limit=int(args.get("limit", 10))
            )
        return {"error": f"Unknown tool: {tool_name}"}

    @classmethod
    async def _execute_llm_tool_loop(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        conversation: AIConversation,
        latest_message: str,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Invokes OpenAI LLM with tool calling loop."""
        settings = get_settings()
        messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Append recent history
        if conversation.messages:
            for m in conversation.messages[-8:]:
                messages.append({"role": m.role, "content": m.content})
        else:
            messages.append({"role": "user", "content": latest_message})

        executed_tools: list[dict[str, Any]] = []

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                payload = {
                    "model": settings.openai_model or "gpt-4o",
                    "messages": messages,
                    "tools": ASSISTANT_TOOL_DEFINITIONS,
                    "tool_choice": "auto",
                    "temperature": 0.2,
                }
                headers = {
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                }

                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()

                choice = data["choices"][0]
                assistant_response = choice["message"]

                # If tool calls were made by LLM
                tool_calls = assistant_response.get("tool_calls")
                if tool_calls:
                    messages.append(assistant_response)
                    for tc in tool_calls:
                        func_name = tc["function"]["name"]
                        func_args = json.loads(tc["function"].get("arguments", "{}"))

                        tool_result = await cls._execute_tool(db, user_id, func_name, func_args)
                        executed_tools.append(
                            {"tool": func_name, "args": func_args, "result": tool_result}
                        )

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tc["id"],
                                "content": json.dumps(tool_result),
                            }
                        )

                    # Second turn to summarize tool execution
                    second_resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        json={"model": settings.openai_model, "messages": messages},
                        headers=headers,
                    )
                    second_resp.raise_for_status()
                    final_text = second_resp.json()["choices"][0]["message"]["content"]
                    return final_text, executed_tools

                return assistant_response.get("content", ""), executed_tools

        except Exception as exc:
            logger.warning("LLM API call failed, falling back to deterministic advisory: %s", exc)
            return await cls._execute_rule_based_advisory(db, user_id, latest_message)

    @classmethod
    async def _execute_rule_based_advisory(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        prompt: str,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Offline deterministic advisor fallback matching financial intents with exact tool data."""
        p_lower = prompt.lower()
        executed_tools: list[dict[str, Any]] = []

        # 1. Purchase reward recommendation intent (e.g. "Which card should I use on Amazon?")
        if any(w in p_lower for w in ["which card", "best card", "card to use", "amazon", "flipkart", "swiggy", "spend", "buy"]):
            # Extract amount or default 5000
            amt_match = re.search(r"(?:rs\.?|inr|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)", prompt)
            amt = 5000.0
            if amt_match:
                cleaned_num = amt_match.group(1).replace(",", "")
                try:
                    val = float(cleaned_num)
                    if val > 0:
                        amt = val
                except ValueError:
                    pass

            merchant = ""
            for m in ["amazon", "flipkart", "swiggy", "zomato", "uber", "myntra", "hpcl", "apple"]:
                if m in p_lower:
                    merchant = m.capitalize()
                    break

            category = "Food & Dining" if merchant in ["Swiggy", "Zomato"] else ("Travel" if merchant == "Uber" else "Shopping")
            if "petrol" in p_lower or "fuel" in p_lower:
                category = "Fuel"
                merchant = merchant or "HPCL"

            res = await AssistantTools.evaluate_purchase_rewards(db, user_id, amount=amt, merchant=merchant, category=category)
            executed_tools.append({"tool": "evaluate_purchase_rewards", "args": {"amount": amt, "merchant": merchant, "category": category}, "result": res})

            rec = res.get("recommended_card")
            if rec:
                reply = (
                    f"### 🏆 Recommended Card: **{rec['card_name']}** ({rec['issuer']})\n\n"
                    f"For a planned spend of **₹{amt:,.2f}** on **{merchant or 'this purchase'}**:\n\n"
                    f"- **Estimated Reward:** `₹{rec['net_reward_inr']:,.2f}`\n"
                    f"- **Effective Rate:** **{rec['effective_rate_percent']:.1f}% return**\n"
                    f"- **Rule Applied:** {rec['explanation']}\n\n"
                    f"**Comparison with your other cards:**\n"
                )
                for c in res.get("all_cards_comparison", []):
                    badge = "⭐ Winner" if c["is_recommended"] else f"Rank #{c['rank']}"
                    reply += f"- **{c['card_name']}** (****{c['last_four']}): ₹{c['net_reward_inr']:,.2f} ({c['effective_rate_percent']:.1f}%) — {badge}\n"
                reply += f"\n> *Note: {res.get('disclaimer')}*"
                return reply, executed_tools
            else:
                return "I couldn't find an eligible active card for this transaction. Please ensure your cards and reward rules are configured.", executed_tools

        # 2. Upcoming dues / bills intent
        if any(w in p_lower for w in ["bill", "due", "pay", "payment", "outstanding", "owe"]):
            res = await AssistantTools.get_upcoming_dues(db, user_id)
            executed_tools.append({"tool": "get_upcoming_dues", "args": {}, "result": res})
            bills = res.get("bills", [])

            if not bills:
                return "✅ You have no active unpaid statements due right now! All your cards are settled.", executed_tools

            reply = "### 💳 Upcoming Credit Card Bills & Dues\n\n"
            for b in bills:
                status_emoji = "🚨 OVERDUE" if b["is_overdue"] else (f"⏰ Due in {b['days_until_due']} days" if b['days_until_due'] >= 0 else "Pending")
                reply += (
                    f"**{b['issuer']} {b['card_name']}** (****{b['last_four']}):\n"
                    f"- **Remaining Balance:** `₹{b['remaining_balance']:,.2f}`\n"
                    f"- **Minimum Due:** `₹{b['minimum_due']:,.2f}`\n"
                    f"- **Due Date:** {b['due_date']} ({status_emoji})\n"
                    f"- **Status:** `{b['status']}`\n\n"
                )
            return reply, executed_tools

        # 3. Spending Analytics intent
        if any(w in p_lower for w in ["spend", "analytics", "category", "month", "how much"]):
            res = await AssistantTools.get_spending_analytics(db, user_id)
            executed_tools.append({"tool": "get_spending_analytics", "args": {}, "result": res})

            delta_str = f"+{res['spend_change_percent']:.1f}%" if res.get('spend_change_percent') and res['spend_change_percent'] > 0 else f"{res.get('spend_change_percent', 0):.1f}%"
            reply = (
                f"### 📊 Spending Analytics Overview\n\n"
                f"- **Current Month Spend:** `₹{res['current_month_spend']:,.2f}`\n"
                f"- **Previous Month Spend:** `₹{res['previous_month_spend']:,.2f}` (Change: `{delta_str}`)\n"
                f"- **Total Outstanding Across Cards:** `₹{res['total_outstanding']:,.2f}`\n"
                f"- **Overall Credit Utilization:** `{res['overall_utilization_percent']:.1f}%`\n\n"
                f"**Top Spending Categories:**\n"
            )
            for cat in res.get("top_categories", []):
                reply += f"- **{cat['category']}:** `₹{cat['spend']:,.2f}` ({cat['percentage']:.1f}%)\n"

            return reply, executed_tools

        # 4. Cap status intent
        if any(w in p_lower for w in ["cap", "limit", "monthly cap", "exhaust"]):
            res = await AssistantTools.get_cap_status(db, user_id)
            executed_tools.append({"tool": "get_cap_status", "args": {}, "result": res})
            caps = res.get("caps", [])
            if not caps:
                return "You currently have no active cap limits configured on your card programs.", executed_tools

            reply = "### 🛡️ Active Reward Cap Utilization\n\n"
            for c in caps:
                reply += (
                    f"**{c['card_name']} — {c['cap_name']}:**\n"
                    f"- **Consumed:** `₹{c['consumed_amount']:,.2f}` / `₹{c['cap_amount']:,.2f}` ({c['utilization_percent']}%)\n"
                    f"- **Remaining:** `₹{c['remaining_amount']:,.2f}`\n"
                    f"- **Resets on:** {c['next_reset_date']}\n\n"
                )
            return reply, executed_tools

        # 5. Missing rewards / audit intent
        if any(w in p_lower for w in ["missing", "lost", "leak", "audit", "excluded", "reconciliation"]):
            res = await AssistantTools.detect_missing_rewards(db, user_id)
            executed_tools.append({"tool": "detect_missing_rewards", "args": {}, "result": res})

            reply = (
                f"### 🔍 Reward Audit & Leakage Detection\n\n"
                f"- **Expected Realized Rewards:** `₹{res['total_expected_rewards_inr']:,.2f}`\n"
                f"- **Excluded Spend (Fuel/Rent):** `₹{res['total_excluded_spend_inr']:,.2f}`\n"
                f"- **Capped Benefit Lost:** `₹{res['total_capped_lost_inr']:,.2f}`\n"
                f"- **Flagged Transactions:** `{res['discrepancy_count']}` items\n\n"
            )
            if res.get("flagged_items"):
                reply += "**Recent Discrepancies:**\n"
                for item in res["flagged_items"][:5]:
                    reply += f"- **{item['date']}** ({item['card']}): {item['description']} (`₹{item['amount']:,.2f}`) — *{item['reason']}*\n"
            return reply, executed_tools

        # 6. Default Card Summary / General query
        res = await AssistantTools.get_card_summary(db, user_id)
        executed_tools.append({"tool": "get_card_summary", "args": {}, "result": res})
        cards = res.get("cards", [])

        reply = (
            f"Hello! I am your **FinSight AI Financial Assistant**.\n\n"
            f"You currently have **{res['total_active_cards']} active credit cards** registered:\n"
        )
        for c in cards:
            reply += f"- **{c['issuer']} {c['card_name']}** (****{c['last_four']}): Balance `₹{c['current_balance']:,.2f}` / Limit `₹{c['credit_limit']:,.2f}` (Util: `{c['utilization_percent']}%`)\n"

        reply += (
            f"\nHere are a few questions you can ask me:\n"
            f"- *'Which card gives the highest cashback for ₹10,000 on Amazon?'*\n"
            f"- *'What are my upcoming credit card dues and due dates?'*\n"
            f"- *'Show my spend breakdown by category this month.'*\n"
            f"- *'Are any of my reward caps close to being exhausted?'*\n"
            f"- *'Did I lose any rewards on my statements due to exclusions?'*"
        )
        return reply, executed_tools
