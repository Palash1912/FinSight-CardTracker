"""Pydantic v2 schemas for document knowledge, policy search, and RAG (Phase 9)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DocumentChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    page_number: int
    content: str
    token_count: int
    metadata_json: dict[str, Any] | None = None


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    card_id: uuid.UUID | None
    title: str
    doc_type: str
    file_name: str
    file_size_bytes: int
    total_pages: int
    status: str
    created_at: datetime
    chunks_count: int = 0


class PolicyCitation(BaseModel):
    """Specific page attribution for grounded policy retrieval."""

    document_id: uuid.UUID
    document_title: str
    doc_type: str
    page_number: int
    snippet: str
    relevance_score: float


class PolicySearchRequest(BaseModel):
    """User query searching bank policy knowledge base."""

    query: str = Field(min_length=2, max_length=500)
    card_id: uuid.UUID | None = None
    limit: int = Field(default=4, ge=1, le=10)


class PolicySearchResponse(BaseModel):
    """Grounded RAG retrieval response with exact source page citations."""

    query: str
    citations: list[PolicyCitation]
    synthesized_explanation: str


class DiscrepancyReportItem(BaseModel):
    """Cross-reference finding between active RewardRule and policy document."""

    card_name: str
    rule_name: str
    configured_rate: str
    policy_document: str
    policy_page: int
    discrepancy_type: str  # devaluation, unconfigured_exclusion, cap_mismatch, rate_conflict
    description: str
    recommended_action: str


class DiscrepancyReportResponse(BaseModel):
    """Audit report comparing active system rules against bank policies."""

    total_discrepancies: int
    items: list[DiscrepancyReportItem]
