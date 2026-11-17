"""Generic fallback credit card statement parser adapter."""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal

from app.parsers.base import BaseStatementParser, ParsedStatementData, RawTransaction


class GenericStatementParser(BaseStatementParser):
    """Fallback parser for statements without an explicit bank-specific adapter."""

    name: str = "generic"

    def can_parse(self, text: str) -> bool:
        # Generic parser can always serve as fallback
        return True

    def _parse_date(self, s: str) -> date | None:
        clean = s.strip().replace("-", "/")
        formats = ["%d/%m/%Y", "%d/%b/%Y", "%Y/%m/%d", "%d/%m/%y"]
        for fmt in formats:
            try:
                return datetime.strptime(clean, fmt).date()
            except ValueError:
                continue
        return None

    def _parse_amount(self, s: str) -> Decimal:
        clean = re.sub(r"[^\d.]", "", s.replace(",", ""))
        try:
            return Decimal(clean)
        except Exception:
            return Decimal("0")

    def parse(self, text: str, pages: list[str] | None = None) -> ParsedStatementData:
        data = ParsedStatementData(issuer="Generic Statement")

        # Statement date detection
        stmt_m = re.search(
            r"(?:Statement Date|Billing Date|Date)\s*[:\s]+(\d{2}[/-]\d{2}[/-]\d{2,4})",
            text,
            re.IGNORECASE,
        )
        if stmt_m:
            data.statement_date = self._parse_date(stmt_m.group(1))

        # Due date detection
        due_m = re.search(
            r"(?:Payment Due Date|Due Date)\s*[:\s]+(\d{2}[/-]\d{2}[/-]\d{2,4})",
            text,
            re.IGNORECASE,
        )
        if due_m:
            data.due_date = self._parse_date(due_m.group(1))

        # Total amount due detection
        due_amt_m = re.search(
            r"(?:Total Amount Due|Total Dues|Closing Balance|New Balance)\s*[:\s]+(?:INR|Rs\.?|₹)?\s*([\d,]+\.?\d*)",
            text,
            re.IGNORECASE,
        )
        if due_amt_m:
            data.total_amount_due = self._parse_amount(due_amt_m.group(1))

        # Card number detection
        card_m = re.search(r"[xX*]{4,12}\s*(\d{4})", text)
        if card_m:
            data.card_last_four = card_m.group(1)

        # Transaction lines scanning
        # Matches: Date ... Description ... Amount [CR/DR]
        lines = text.split("\n")
        row_num = 0
        total_debits = Decimal("0")
        total_credits = Decimal("0")

        txn_re = re.compile(
            r"^(\d{2}[/-]\d{2}[/-]\d{2,4})\s+(.+?)\s+([\d,]+\.\d{2})\s*(CR|DR|Cr|Dr)?$",
            re.IGNORECASE,
        )

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            match = txn_re.search(line_str)
            if match:
                dt_str, desc, amt_str, indicator = match.groups()
                txn_date = self._parse_date(dt_str)
                if not txn_date:
                    continue

                amount = self._parse_amount(amt_str)
                if amount <= 0:
                    continue

                is_credit = False
                if indicator and indicator.upper() == "CR":
                    is_credit = True
                elif any(kw in desc.upper() for kw in ("PAYMENT", "REFUND", "CR RECEIVED")):
                    is_credit = True

                txn_type = "credit" if is_credit else "debit"
                if txn_type == "debit":
                    total_debits += amount
                else:
                    total_credits += amount

                row_num += 1
                data.transactions.append(
                    RawTransaction(
                        date=txn_date,
                        description=desc.strip(),
                        amount=amount,
                        txn_type=txn_type,
                        source_row=row_num,
                        raw_text=line_str,
                    )
                )

        data.total_debits = total_debits
        data.total_credits = total_credits
        return data
