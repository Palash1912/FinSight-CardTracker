"""Unit tests for Phase 9: Document chunking, policy RAG relevance, and schemas."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.schemas.document import (
    DiscrepancyReportItem,
    DocumentChunkRead,
    DocumentRead,
    PolicyCitation,
    PolicySearchResponse,
)
from app.services.document_service import chunk_text
from app.services.policy_rag import compute_chunk_relevance


def test_chunk_text_algorithm() -> None:
    sample = " ".join([f"word{i}" for i in range(100)])
    chunks = chunk_text(sample, page_number=2, chunk_size_words=30, overlap_words=5)

    assert len(chunks) >= 4
    for c in chunks:
        assert c["page_number"] == 2
        assert c["token_count"] <= 30
        assert len(c["content"]) > 0


def test_chunk_relevance_scoring() -> None:
    content = "Fuel purchases at petrol pumps and rent payments are strictly excluded from reward points."
    title = "HDFC Millennia Rewards Policy"

    score_fuel = compute_chunk_relevance(["fuel", "excluded"], content, title)
    assert score_fuel > 2.0

    score_title = compute_chunk_relevance(["millennia"], content, title)
    assert score_title >= 3.0  # title match boost

    score_irrelevant = compute_chunk_relevance(["cryptocurrency"], content, title)
    assert score_irrelevant == 0.0


def test_document_schemas() -> None:
    doc_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    doc = DocumentRead(
        id=doc_id,
        card_id=None,
        title="Amazon Pay Terms",
        doc_type="policy",
        file_name="amazon_pay_terms.pdf",
        file_size_bytes=45000,
        total_pages=3,
        status="processed",
        created_at=now,
        chunks_count=6,
    )
    assert doc.title == "Amazon Pay Terms"
    assert doc.total_pages == 3

    citation = PolicyCitation(
        document_id=doc_id,
        document_title="Amazon Pay Terms",
        doc_type="policy",
        page_number=2,
        snippet="Fuel and rent are excluded from cashback.",
        relevance_score=4.5,
    )
    assert citation.page_number == 2
    assert citation.relevance_score == 4.5

    discrepancy = DiscrepancyReportItem(
        card_name="Millennia",
        rule_name="5% Accelerator",
        configured_rate="5.0%",
        policy_document="HDFC Policy Circular",
        policy_page=3,
        discrepancy_type="unconfigured_exclusion",
        description="Policy excludes Rent on page 3.",
        recommended_action="Add Rent to exclusions.",
    )
    assert discrepancy.discrepancy_type == "unconfigured_exclusion"
