"""
this package includes high-level tests for cost operatinos
"""

import asyncio
import json
from datetime import timedelta

import httpx
import pytest
from fastapi import status

from src import domain, http
from src.infrastructure import database


# ==================================================
# tests for not authorized
# ==================================================
async def test_cost_categories_fetch_anonymous(anonymous: httpx.AsyncClient):
    response = await anonymous.get("/costs/categories")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_cost_categories_create_anonymous(anonymous: httpx.AsyncClient):
    response = await anonymous.post("/costs/categories", json={"name": "..."})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_cost_update_anonymous(anonymous: httpx.AsyncClient):
    response = await anonymous.patch("/costs/1", json={"name": "..."})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_cost_delete_anonymous(anonymous: httpx.AsyncClient):
    response = await anonymous.patch("/costs/1", json={"name": "..."})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================================================
# tests for authorized user
# ==================================================
@pytest.mark.use_db
async def test_cost_categories_fetch(
    client: httpx.AsyncClient, cost_categories
):
    response = await client.get("/costs/categories")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["result"]) == len(cost_categories)


@pytest.mark.use_db
async def test_cost_category_creation(
    client: httpx.AsyncClient, cost_categories
):
    response = await client.post(
        "/costs/categories", json={"name": "Another yet category"}
    )

    total = await domain.transactions.TransactionRepository().count(
        database.CostCategory
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert total == len(cost_categories) + 1


@pytest.mark.use_db
async def test_costs_fetch(client: httpx.AsyncClient, cost_factory):
    """test response paginated by default."""

    costs: list[database.Cost] = await cost_factory(n=15)

    response1: httpx.Response = await client.get("/costs")
    response1_data = response1.json()
    response2: httpx.Response = await client.get(
        "/costs", params={"context": response1_data["context"]}
    )
    response2_data = response2.json()

    total = await domain.transactions.TransactionRepository().count(
        database.Cost
    )

    assert total == len(costs)
    assert response1.status_code == status.HTTP_200_OK
    assert response2.status_code == status.HTTP_200_OK
    assert len(response1_data["result"]) == 10
    assert len(response2_data["result"]) == 5
    assert response1_data["context"] == 10
    assert response2_data["context"] == 15
    assert response1_data["left"] == 5
    assert response2_data["left"] == 0


@pytest.mark.use_db
async def test_cost_add(
    client: httpx.AsyncClient, cost_categories, currencies
):
    response: httpx.Response = await client.post(
        "/costs",
        json={
            "name": "PS5",
            "value": 100,  # value is not in cents
            "currencyId": 1,
            "categoryId": 1,
        },
    )

    total = await domain.transactions.TransactionRepository().count(
        database.Cost
    )

    currency: database.Currency = (
        await domain.equity.EquityRepository().currency(id_=1)
    )

    assert response.status_code == status.HTTP_201_CREATED, response.json()
    assert total == 1
    assert currency.equity == currencies[0].equity - 10000


@pytest.mark.use_db
async def test_cost_update_safe(
    client: httpx.AsyncClient, currencies, cost_factory
):
    """test operations that should not change the equity."""

    cost, *_ = await cost_factory(n=1)
    body = http.CostUpdateBody(
        name="".join((cost.name, "some salt")),
        category_id=2,  # `1` by default
        timestamp=cost.timestamp - timedelta(days=3),
    )
    response = await client.patch(
        f"/costs/{cost.id}", json=json.loads(body.json(exclude_unset=True))
    )

    currency: database.Currency = (
        await domain.equity.EquityRepository().currency(id_=1)
    )

    updated_instance = await domain.transactions.TransactionRepository().cost(
        id_=cost.id
    )

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert currency.equity == currencies[0].equity
    for attr in {"name", "category_id", "timestamp"}:
        assert getattr(updated_instance, attr) == getattr(body, attr)


@pytest.mark.use_db
async def test_cost_update_only_value_increased(
    client: httpx.AsyncClient, currencies, cost_factory
):
    cost, *_ = await cost_factory(n=1)
    new_value = cost.value + 10000
    response = await client.patch(
        f"/costs/{cost.id}", json={"value": new_value / 100}
    )

    currency: database.Currency = (
        await domain.equity.EquityRepository().currency(id_=1)
    )
    updated_instance = await domain.transactions.TransactionRepository().cost(
        id_=cost.id
    )

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert currency.equity == cost.value - new_value
    assert updated_instance.value == new_value


@pytest.mark.use_db
async def test_cost_update_only_currency(
    client: httpx.AsyncClient, currencies, cost_factory
):
    cost, *_ = await cost_factory(n=1)
    new_currency_id = 2
    response = await client.patch(
        f"/costs/{cost.id}", json={"currency_id": new_currency_id}
    )

    src_currency, dst_currency = await asyncio.gather(
        domain.equity.EquityRepository().currency(id_=cost.currency_id),
        domain.equity.EquityRepository().currency(id_=new_currency_id),
    )

    updated_instance = await domain.transactions.TransactionRepository().cost(
        id_=cost.id
    )

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert src_currency.equity == currencies[0].equity + cost.value
    assert dst_currency.equity == currencies[1].equity - cost.value
    assert updated_instance.currency_id == new_currency_id


@pytest.mark.use_db
async def test_cost_update_currency_and_value(
    client: httpx.AsyncClient, currencies, cost_factory
):
    """upadte value and currency.

    workflow:
        increase the cost value for 100.00
        HTTP PATCH /costs/id to update the item in the database
    """

    cost, *_ = await cost_factory(n=1)
    payload = {"value": cost.value / 100 + 100.00, "currency_id": 2}
    response = await client.patch(f"/costs/{cost.id}", json=payload)

    src_currency, dst_currency = await asyncio.gather(
        domain.equity.EquityRepository().currency(id_=cost.currency_id),
        domain.equity.EquityRepository().currency(id_=payload["currency_id"]),
    )

    updated_instance = await domain.transactions.TransactionRepository().cost(
        id_=cost.id
    )

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert src_currency.equity == cost.value  # increase for an old value
    assert dst_currency.equity == -(
        cost.value + 10000
    )  # decrease for a new value
    assert updated_instance.currency_id == payload["currency_id"]


@pytest.mark.use_db
async def test_cost_delete(
    client: httpx.AsyncClient, currencies, cost_factory
):
    """
    WORKFLOW
    1. delete cost
    2. wait for cost to be deleted in background
    3. check database state
    """
    cost, *_ = await cost_factory(n=1)
    response = await client.delete(f"/costs/{cost.id}")

    await asyncio.sleep(0.1)

    currency = await domain.equity.EquityRepository().currency(
        id_=cost.currency_id
    )

    total = await domain.transactions.TransactionRepository().count(
        database.Cost
    )

    assert total == 0
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.json()
    assert currency.equity == currencies[0].equity + cost.value


# ==================================================
# tests for validation
# ==================================================
@pytest.mark.parametrize(
    "payload,error_type",
    [
        ({}, "missing"),
        ({"name": None}, "bad-type"),
        ({"name": 12}, "bad-type"),
        ({"anotherField": "proper string"}, "missing"),
    ],
)
@pytest.mark.use_db
async def test_cost_category_creation_unprocessable(
    client: httpx.AsyncClient, payload, error_type
):
    response = await client.post("/costs/categories", json=payload)

    total = await domain.transactions.TransactionRepository().count(
        database.CostCategory
    )

    assert (
        response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    ), payload
    assert (
        response.json()["result"][0]["detail"]["type"] == error_type
    ), response.json()
    assert total == 0


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": None},
        {"anotherField": "proper string"},
        {
            "name": "correct",
            "value": "not valid integer",
            "currencyId": 1,
            "categoryId": 1,
        },
        {
            "name": "correct",
            "value": -1,  # negative
            "currencyId": 1,
            "categoryId": 1,
        },
        {
            "name": "correct",
            "value": 100,
            "currencyId": None,  # invalid
            "categoryId": None,  # invalid
        },
    ],
)
@pytest.mark.use_db
async def test_cost_creation_unprocessable(client: httpx.AsyncClient, payload):
    response = await client.post("/costs", json=payload)

    total = await domain.transactions.TransactionRepository().count(
        database.Cost
    )

    assert (
        response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    ), response.json()
    assert total == 0
