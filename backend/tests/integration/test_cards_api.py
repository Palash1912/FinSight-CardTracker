"""API tests for /api/v1/cards (run against in-memory SQLite)."""

from __future__ import annotations

import uuid
from decimal import Decimal

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import CreditCard, User

BASE = "/api/v1/cards"


def _card_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "issuer": "HDFC Bank",
        "card_name": "Regalia",
        "network": "mastercard",
        "last_four_digits": "5678",
        "billing_cycle_day": 10,
        "payment_due_days": 20,
        "credit_limit": "200000.00",
        "current_balance": "45000.50",
        "annual_fee": "2500",
    }
    payload.update(overrides)
    return payload


async def _create(client: httpx.AsyncClient, **overrides: object) -> dict[str, object]:
    response = await client.post(BASE, json=_card_payload(**overrides))
    assert response.status_code == 201, response.text
    body: dict[str, object] = response.json()
    return body


async def test_create_card_returns_snake_case_with_computed_fields(
    api_client: httpx.AsyncClient,
) -> None:
    card = await _create(api_client)

    assert card["issuer"] == "HDFC Bank"
    assert card["last_four_digits"] == "5678"
    assert card["status"] == "active"
    assert Decimal(card["available_credit"]) == Decimal("154999.50")
    assert "next_statement_date" in card and "next_due_date" in card
    assert "creditLimit" not in card  # snake_case contract


async def test_list_hides_archived_cards_by_default(api_client: httpx.AsyncClient) -> None:
    active = await _create(api_client, last_four_digits="1111")
    to_archive = await _create(api_client, last_four_digits="2222")

    archived = await api_client.post(f"{BASE}/{to_archive['id']}/archive")
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"

    listed = (await api_client.get(BASE)).json()
    assert [c["id"] for c in listed] == [active["id"]]

    everything = (await api_client.get(BASE, params={"include_archived": True})).json()
    assert len(everything) == 2


async def test_get_and_partial_update(api_client: httpx.AsyncClient) -> None:
    card = await _create(api_client)

    fetched = await api_client.get(f"{BASE}/{card['id']}")
    assert fetched.status_code == 200

    updated = await api_client.patch(
        f"{BASE}/{card['id']}", json={"card_name": "Regalia Gold", "current_balance": "0"}
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["card_name"] == "Regalia Gold"
    assert Decimal(body["current_balance"]) == Decimal("0")
    assert body["issuer"] == "HDFC Bank"  # untouched fields preserved


async def test_patch_rejects_invalid_values(api_client: httpx.AsyncClient) -> None:
    card = await _create(api_client)
    response = await api_client.patch(f"{BASE}/{card['id']}", json={"billing_cycle_day": 31})
    assert response.status_code == 422


async def test_unknown_card_returns_404(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get(f"{BASE}/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_create_rejects_invalid_payload(api_client: httpx.AsyncClient) -> None:
    response = await api_client.post(BASE, json=_card_payload(last_four_digits="abcd"))
    assert response.status_code == 422


async def test_cards_of_other_users_are_not_visible(
    api_client: httpx.AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    other_user_id = uuid.uuid4()
    async with session_factory() as session:
        session.add(User(id=other_user_id, email="someone.else@example.com", is_active=True))
        foreign_card = CreditCard(
            user_id=other_user_id,
            issuer="Axis Bank",
            card_name="Magnus",
            network="visa",
            last_four_digits="9999",
            billing_cycle_day=5,
            payment_due_days=20,
            credit_limit=500000,
            status="active",
        )
        session.add(foreign_card)
        await session.commit()
        foreign_id = foreign_card.id

    assert (await api_client.get(BASE)).json() == []
    assert (await api_client.get(f"{BASE}/{foreign_id}")).status_code == 404
    assert (
        await api_client.patch(f"{BASE}/{foreign_id}", json={"status": "archived"})
    ).status_code == 404
