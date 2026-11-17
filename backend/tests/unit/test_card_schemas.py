"""Validation tests for card request schemas."""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.card import CardCreate, CardUpdate


def _valid_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "issuer": "ICICI Bank",
        "card_name": "Amazon Pay",
        "network": "visa",
        "last_four_digits": "1234",
        "billing_cycle_day": 15,
        "payment_due_days": 20,
        "credit_limit": "150000",
    }
    payload.update(overrides)
    return payload


def test_valid_create_payload_is_accepted() -> None:
    card = CardCreate.model_validate(_valid_payload())
    assert card.credit_limit == Decimal("150000")
    assert card.current_balance == Decimal("0")


@pytest.mark.parametrize(
    "overrides",
    [
        {"last_four_digits": "12345"},  # too long
        {"last_four_digits": "12a4"},  # not digits
        {"network": "discover"},  # unsupported network
        {"billing_cycle_day": 29},  # avoid month-end ambiguity
        {"payment_due_days": 0},
        {"credit_limit": "0"},  # must be positive
        {"current_balance": "-1"},  # balance cannot be negative
        {"credit_limit": "1.123456"},  # more than 4 decimal places
    ],
)
def test_invalid_create_payloads_are_rejected(overrides: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        CardCreate.model_validate(_valid_payload(**overrides))


def test_update_accepts_partial_payload() -> None:
    update = CardUpdate.model_validate({"card_name": "Amazon Pay Gold"})
    assert update.model_dump(exclude_unset=True) == {"card_name": "Amazon Pay Gold"}


def test_update_rejects_explicit_null_for_required_field() -> None:
    with pytest.raises(ValidationError):
        CardUpdate.model_validate({"credit_limit": None})


def test_update_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        CardUpdate.model_validate({"card_number": "4111111111111111"})
