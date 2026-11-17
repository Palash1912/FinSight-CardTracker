"""HSBC Credit Card statement parser adapter."""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal

from app.parsers.base import BaseStatementParser, ParsedStatementData, RawTransaction


class HSBCStatementParser(BaseStatementParser):
    """Parser adapter for HSBC credit card statements."""

    name: str = "hsbc"

    def can_parse(self, text: str) -> bool:
        lower = text.lower()
        return "hsbc" in lower and ("card" in lower or "statement" in lower)

    def _parse_date(self, date_str: str) -> date | None:
        clean = date_str.replace("-", "/")
        try:
            return datetime.strptime(clean, "%d/%m/%Y").date()
        except ValueError:
            return None

    def _parse_amount(self, amt_str: str) -> Decimal:
        clean = amt_str.replace(",", "").strip()
        try:
            return Decimal(clean)
        except Exception:
            return Decimal("0")

    def parse(self, text: str, pages: list[str] | None = None) -> ParsedStatementData:
        data = ParsedStatementData(issuer="HSBC")

        # 1. Statement Date
        stmt_date_match = re.search(
            r"Statement Date\s*[:\s]+(\d{2}[/-]\d{2}[/-]\d{4})", text, re.IGNORECASE
        )
        if stmt_date_match:
            data.statement_date = self._parse_date(stmt_date_match.group(1))

        # 2. Payment Due Date
        due_date_match = re.search(
            r"Payment Due Date\s*[:\s]+(\d{2}[/-]\d{2}[/-]\d{4})", text, re.IGNORECASE
        )
        if due_date_match:
            data.due_date = self._parse_date(due_date_match.group(1))

        # 3. Card Number Last 4
        card_match = re.search(
            r"(?:Card Number|Account Number)[^\n\d]*[xX*]+(\d{4})", text, re.IGNORECASE
        )
        if card_match:
            data.card_last_four = card_match.group(1)

        # 4. Closing Balance / Total Payment Due
        total_due_match = re.search(
            r"(?:Total Payment Due|Closing Balance)\s*[:\s]+(?:INR|Rs\.?|₹)?\s*([\d,]+\.?\d*)",
            text,
            re.IGNORECASE,
        )
        if total_due_match:
            data.total_amount_due = self._parse_amount(total_due_match.group(1))

        min_due_match = re.search(
            r"Minimum Payment Due\s*[:\s]+(?:INR|Rs\.?|₹)?\s*([\d,]+\.?\d*)",
            text,
            re.IGNORECASE,
        )
        if min_due_match:
            data.minimum_amount_due = self._parse_amount(min_due_match.group(1))

        # 5. Extract Transactions
        lines = text.split("\n")
        row_num = 0
        total_debits = Decimal("0")
        total_credits = Decimal("0")

        txn_re = re.compile(
            r"^(\d{2}[/-]\d{2}[/-]\d{4})\s+(.+?)\s+([\d,]+\.\d{2})\s*(CR|DR)?$",
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
                is_credit = False
                if indicator and indicator.upper() == "CR":
                    is_credit = True
                elif "PAYMENT" in desc.upper() or "CREDIT" in desc.upper():
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
