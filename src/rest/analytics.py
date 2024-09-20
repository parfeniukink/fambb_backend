from typing import Annotated

from fastapi import APIRouter, Query, status

from src import contracts, domain, operations
from src.infrastructure import ResponseMulti

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/equity", status_code=status.HTTP_200_OK)
async def equity() -> ResponseMulti[contracts.Equity]:
    """Expose the ``equity``, related to each currency."""

    return ResponseMulti[contracts.Equity](
        result=[
            contracts.Equity.from_instance(item)
            async for item in domain.finances.FinancialRepository().currencies()
        ]
    )


@router.get("/transactions", status_code=status.HTTP_200_OK)
async def transactions(
    currency: Annotated[
        int | None,
        Query(description="ID of a currency to filter. Skip to ignore."),
    ] = None,
) -> ResponseMulti[contracts.Transaction]:
    """Expose last transactions, not filtered but limited with Settings."""

    return ResponseMulti[contracts.Transaction](
        result=[
            contracts.Transaction.from_instance(item)
            async for item in operations.get_transactions(currency_id=currency)
        ]
    )


@router.get("/transactions/last", status_code=status.HTTP_200_OK)
async def transactions_last() -> ResponseMulti[contracts.Transaction]:
    """Expose last transactions, not filtered but limited with Settings."""

    return ResponseMulti[contracts.Transaction](
        result=[
            contracts.Transaction.from_instance(item)
            async for item in operations.get_last_transactions()
        ]
    )
