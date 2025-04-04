from fastapi import APIRouter, Body, Depends, status

from src import operational as op
from src.domain import equity as domain
from src.infrastructure import Response, ResponseMulti, database

from ..contracts import Currency, CurrencyCreateBody

router = APIRouter(prefix="/currencies", tags=["Currencies"])


@router.get("", status_code=status.HTTP_200_OK)
async def currencies(_=Depends(op.authorize)) -> ResponseMulti[Currency]:
    """Return available cost categories."""

    currencies: tuple[database.Currency, ...] = (
        await domain.EquityRepository().currencies()
    )

    return ResponseMulti[Currency](
        result=[Currency.from_instance(item) for item in currencies]
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def currency_create(
    _=Depends(op.authorize),
    body: CurrencyCreateBody = Body(...),
) -> Response[Currency]:
    """Create yet another equity."""

    async with database.transaction():
        instance = await domain.EquityRepository().add_currency(
            candidate=database.Currency(name=body.name, sign=body.sign)
        )

    return Response[Currency](result=Currency.from_instance(instance))
