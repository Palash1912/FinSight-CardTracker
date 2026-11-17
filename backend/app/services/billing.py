"""Pure billing-cycle date calculations for credit cards.

A card's statement is generated on `billing_cycle_day` of every month (clamped to
the last day of shorter months). The payment is due `payment_due_days` after the
statement date. No I/O here — everything takes `as_of` explicitly so it is testable.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta


def _statement_date_in(year: int, month: int, billing_cycle_day: int) -> date:
    """Statement date for a given month, clamped to the month's last day."""
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(billing_cycle_day, last_day))


def next_statement_date(billing_cycle_day: int, as_of: date) -> date:
    """Earliest statement date on or after `as_of`."""
    this_month = _statement_date_in(as_of.year, as_of.month, billing_cycle_day)
    if this_month >= as_of:
        return this_month
    if as_of.month == 12:
        return _statement_date_in(as_of.year + 1, 1, billing_cycle_day)
    return _statement_date_in(as_of.year, as_of.month + 1, billing_cycle_day)


def previous_statement_date(billing_cycle_day: int, statement_date: date) -> date:
    """Statement date of the month before `statement_date`."""
    if statement_date.month == 1:
        return _statement_date_in(statement_date.year - 1, 12, billing_cycle_day)
    return _statement_date_in(statement_date.year, statement_date.month - 1, billing_cycle_day)


def current_cycle(billing_cycle_day: int, as_of: date) -> tuple[date, date]:
    """Open billing cycle containing `as_of`, as (start, end) inclusive.

    The cycle ends on the next statement date and starts the day after the previous one.
    """
    end = next_statement_date(billing_cycle_day, as_of)
    previous_end = previous_statement_date(billing_cycle_day, end)
    return previous_end + timedelta(days=1), end


def payment_due_date(statement_date: date, payment_due_days: int) -> date:
    """Payment due date for a statement generated on `statement_date`."""
    return statement_date + timedelta(days=payment_due_days)
