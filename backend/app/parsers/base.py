"""Base parser interface and data structures for credit card statements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Literal


@dataclass
class RawTransaction:
    """A single raw transaction extracted from a statement document."""

    date: date
    description: str
    amount: Decimal
    txn_type: Literal["debit", "credit"]
    posting_date: date | None = None
    source_page: int | None = None
    source_row: int | None = None
    raw_text: str = ""


@dataclass
class ParsedStatementData:
    """Extracted data from a bank statement."""

    issuer: str
    transactions: list[RawTransaction] = field(default_factory=list)
    statement_date: date | None = None
    due_date: date | None = None
    period_start: date | None = None
    period_end: date | None = None
    total_amount_due: Decimal | None = None
    minimum_amount_due: Decimal | None = None
    opening_balance: Decimal | None = None
    closing_balance: Decimal | None = None
    total_credits: Decimal | None = None
    total_debits: Decimal | None = None
    card_last_four: str | None = None
    raw_metadata: dict[str, Any] = field(default_factory=dict)


class BaseStatementParser(ABC):
    """Abstract adapter for a specific bank or format."""

    name: str = "base"

    @abstractmethod
    def can_parse(self, text: str) -> bool:
        """Check if this parser can handle the extracted statement text."""
        pass

    @abstractmethod
    def parse(self, text: str, pages: list[str] | None = None) -> ParsedStatementData:
        """Extract statement metadata and normalized transactions from the text."""
        pass
