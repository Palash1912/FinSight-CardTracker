"""Policy RAG retriever and rule discrepancy auditing engine (Phase 9)."""

from __future__ import annotations

import re
import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.card import CreditCard
from app.models.document import Document, DocumentChunk
from app.models.reward import RewardProgram, RewardRule
from app.schemas.document import (
    DiscrepancyReportItem,
    DiscrepancyReportResponse,
    PolicyCitation,
    PolicySearchRequest,
    PolicySearchResponse,
)

STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "for", "to", "of", "and", "or",
    "is", "are", "do", "does", "what", "how", "can", "my", "card", "with",
}


def compute_chunk_relevance(query_terms: list[str], content: str, title: str) -> float:
    """Computes hybrid relevance score based on term frequencies and phrase matching."""
    c_lower = content.lower()
    t_lower = title.lower()

    score = 0.0
    for term in query_terms:
        # Title match boost
        if term in t_lower:
            score += 3.0
        # Content occurrences
        occurrences = c_lower.count(term)
        if occurrences > 0:
            score += 1.0 + (0.5 * min(occurrences, 4))

    # Exact multi-word match boost
    full_phrase = " ".join(query_terms)
    if len(query_terms) > 1 and full_phrase in c_lower:
        score += 5.0

    return score


class PolicyRAGService:
    """Provides grounded knowledge retrieval with page citations and rule discrepancy detection."""

    @classmethod
    async def search_policies(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        req: PolicySearchRequest,
    ) -> PolicySearchResponse:
        """Search policy documents and return exact page-attributed citations."""
        # Query chunks for user's documents
        stmt = (
            select(DocumentChunk)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.user_id == user_id, Document.status == "processed")
            .options(selectinload(DocumentChunk.document))
        )
        if req.card_id:
            stmt = stmt.where(Document.card_id == req.card_id)

        chunks = list((await db.execute(stmt)).scalars().all())

        if not chunks:
            return PolicySearchResponse(
                query=req.query,
                citations=[],
                synthesized_explanation=(
                    "No policy documents found in your knowledge base. "
                    "Upload card terms and agreements or click 'Seed Default Bank Policies' to enable grounded answers."
                ),
            )

        # Tokenize query
        cleaned_words = [
            w for w in re.findall(r"\w+", req.query.lower()) if w not in STOP_WORDS and len(w) > 2
        ]
        if not cleaned_words:
            cleaned_words = [w for w in re.findall(r"\w+", req.query.lower())]

        scored: list[tuple[DocumentChunk, float]] = []
        for ch in chunks:
            score = compute_chunk_relevance(cleaned_words, ch.content, ch.document.title)
            if score > 0:
                scored.append((ch, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        top_matches = scored[: req.limit]

        citations: list[PolicyCitation] = []
        for ch, score in top_matches:
            # Highlight snippet
            content = ch.content.strip()
            snippet = content[:300] + "..." if len(content) > 300 else content

            citations.append(
                PolicyCitation(
                    document_id=ch.document.id,
                    document_title=ch.document.title,
                    doc_type=ch.document.doc_type,
                    page_number=ch.page_number,
                    snippet=snippet,
                    relevance_score=round(score, 2),
                )
            )

        # Grounded synthesis
        if citations:
            best = citations[0]
            explanation = (
                f"Based on **{best.document_title} (Page {best.page_number})**:\n\n"
                f"\"{best.snippet}\"\n\n"
                f"> **Source Verification**: Grounded in official issuer policy terms. "
                f"Found {len(citations)} relevant page references."
            )
        else:
            explanation = (
                f"I searched {len(chunks)} policy document pages for '{req.query}', "
                f"but could not find a high-confidence match. Check your uploaded terms and circulars."
            )

        return PolicySearchResponse(
            query=req.query,
            citations=citations,
            synthesized_explanation=explanation,
        )

    @classmethod
    async def audit_discrepancies(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        card_id: uuid.UUID | None = None,
    ) -> DiscrepancyReportResponse:
        """Cross-references configured RewardRules against official policy document text."""
        # Fetch user's active cards and rules
        prog_stmt = (
            select(RewardProgram)
            .where(RewardProgram.user_id == user_id)
            .options(
                selectinload(RewardProgram.rules).selectinload(RewardRule.caps)
            )
        )
        programs = list((await db.execute(prog_stmt)).scalars().all())

        # Fetch documents with chunks
        doc_stmt = (
            select(Document)
            .where(Document.user_id == user_id, Document.status == "processed")
            .options(selectinload(Document.chunks))
        )
        if card_id:
            doc_stmt = doc_stmt.where(Document.card_id == card_id)
        docs = list((await db.execute(doc_stmt)).scalars().all())

        doc_by_card: dict[uuid.UUID, list[Document]] = {}
        for d in docs:
            if d.card_id:
                doc_by_card.setdefault(d.card_id, []).append(d)

        discrepancies: list[DiscrepancyReportItem] = []

        for prog in programs:
            card_docs = doc_by_card.get(prog.card_id, [])
            if not card_docs:
                continue

            # Concatenate policy text
            all_policy_chunks = []
            for d in card_docs:
                for ch in d.chunks:
                    all_policy_chunks.append((d, ch))

            for rule in prog.rules:
                configured_exclusions = [e.lower() for e in (rule.exclusions or [])]

                # Check for critical bank exclusions mentioned in policy that are missing in rule
                common_exclusions = ["fuel", "rent", "wallet", "jewellery", "government", "education"]
                for excl in common_exclusions:
                    # Check if policy explicitly excludes this
                    for doc_ref, chunk_ref in all_policy_chunks:
                        c_text = chunk_ref.content.lower()
                        if excl in c_text and ("excluded" in c_text or "do not qualify" in c_text or "not eligible" in c_text):
                            if not any(excl in ce for ce in configured_exclusions):
                                discrepancies.append(
                                    DiscrepancyReportItem(
                                        card_name=prog.program_name,
                                        rule_name=rule.rule_name,
                                        configured_rate=f"{float(rule.reward_rate * 100):.1f}%",
                                        policy_document=doc_ref.title,
                                        policy_page=chunk_ref.page_number,
                                        discrepancy_type="unconfigured_exclusion",
                                        description=(
                                            f"Policy explicitly marks '{excl.capitalize()}' as excluded on Page {chunk_ref.page_number}, "
                                            f"but rule '{rule.rule_name}' does not list '{excl.capitalize()}' in exclusions."
                                        ),
                                        recommended_action=f"Update rule exclusions to include '{excl.capitalize()}'.",
                                    )
                                )
                                break

                # Check for monthly cap in policy vs rule caps
                for doc_ref, chunk_ref in all_policy_chunks:
                    c_text = chunk_ref.content.lower()
                    if "cap of" in c_text or "maximum" in c_text and "cashpoints" in c_text:
                        if not rule.caps and rule.rule_type != "base":
                            discrepancies.append(
                                DiscrepancyReportItem(
                                    card_name=prog.program_name,
                                    rule_name=rule.rule_name,
                                    configured_rate=f"{float(rule.reward_rate * 100):.1f}%",
                                    policy_document=doc_ref.title,
                                    policy_page=chunk_ref.page_number,
                                    discrepancy_type="cap_mismatch",
                                    description=(
                                        f"Policy document indicates spend cap restrictions on Page {chunk_ref.page_number}, "
                                        f"but rule has no active cap configured."
                                    ),
                                    recommended_action="Configure a monthly/statement cycle reward cap on this rule.",
                                )
                            )
                            break

        return DiscrepancyReportResponse(
            total_discrepancies=len(discrepancies),
            items=discrepancies,
        )
