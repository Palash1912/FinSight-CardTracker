"""Unit tests for billing-cycle date calculations (pure functions, no DB)."""

from __future__ import annotations

from datetime import date

import pytest

from app.services.billing import (
    current_cycle,
    next_statement_date,
    payment_due_date,
    previous_statement_date,
)


@pytest.mark.parametrize(
    ("billing_day", "as_of", "expected"),
    [
        (15, date(2026, 11, 10), date(2026, 11, 15)),  # before this month's statement
        (15, date(2026, 11, 15), date(2026, 11, 15)),  # on the statement day itself
        (15, date(2026, 11, 16), date(2026, 12, 15)),  # after it -> next month
        (28, date(2026, 12, 29), date(2027, 1, 28)),  # year rollover
        (28, date(2026, 2, 1), date(2026, 2, 28)),  # February
    ],
)
def test_next_statement_date(billing_day: int, as_of: date, expected: date) -> None:
    assert next_statement_date(billing_day, as_of) == expected


def test_previous_statement_date_wraps_year() -> None:
    assert previous_statement_date(10, date(2027, 1, 10)) == date(2026, 12, 10)


def test_current_cycle_spans_previous_statement_plus_one_to_next() -> None:
    start, end = current_cycle(15, date(2026, 11, 20))
    assert end == date(2026, 12, 15)
    assert start == date(2026, 11, 16)


def test_current_cycle_on_statement_day_ends_that_day() -> None:
    start, end = current_cycle(15, date(2026, 11, 15))
    assert end == date(2026, 11, 15)
    assert start == date(2026, 10, 16)


def test_payment_due_date_adds_days() -> None:
    assert payment_due_date(date(2026, 11, 15), 20) == date(2026, 12, 5)
