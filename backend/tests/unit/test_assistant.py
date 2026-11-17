"""Unit tests for Phase 8: AI Financial Assistant schemas and tool definitions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.schemas.assistant import (
    AIConversationRead,
    ChatMessageRead,
    ChatRequest,
    ChatResponse,
)
from app.services.assistant_service import SYSTEM_PROMPT
from app.services.assistant_tools import ASSISTANT_TOOL_DEFINITIONS


def test_assistant_tool_definitions() -> None:
    tool_names = [t["function"]["name"] for t in ASSISTANT_TOOL_DEFINITIONS]
    expected_tools = [
        "get_card_summary",
        "get_upcoming_dues",
        "get_spending_analytics",
        "evaluate_purchase_rewards",
        "get_cap_status",
        "detect_missing_rewards",
        "search_transactions",
    ]
    for exp in expected_tools:
        assert exp in tool_names, f"Expected tool {exp} not found in definitions"


def test_system_prompt_principles() -> None:
    assert "NEVER do mental math" in SYSTEM_PROMPT
    assert "Indian Rupees" in SYSTEM_PROMPT
    assert "deterministic tools" in SYSTEM_PROMPT


def test_assistant_schemas() -> None:
    now = datetime.now(timezone.utc)
    conv_id = uuid.uuid4()
    msg_id = uuid.uuid4()

    req = ChatRequest(
        conversation_id=conv_id,
        message="Which card should I use on Amazon for ₹10,000?",
    )
    assert req.conversation_id == conv_id
    assert "Amazon" in req.message

    msg = ChatMessageRead(
        id=msg_id,
        role="assistant",
        content="Use ICICI Amazon Pay for 5% cashback.",
        tool_calls=[{"tool": "evaluate_purchase_rewards", "args": {"amount": 10000}}],
        tool_call_id=None,
        created_at=now,
    )
    assert msg.role == "assistant"
    assert msg.tool_calls is not None

    resp = ChatResponse(
        conversation_id=conv_id,
        message=msg,
        tool_calls_executed=[{"tool": "evaluate_purchase_rewards"}],
    )
    assert resp.conversation_id == conv_id
    assert resp.message.id == msg_id
