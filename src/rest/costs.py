from fastapi import APIRouter, Body, Depends, status

from src import domain
from src import operational as op
from src.contracts import (
    Cost,
    CostCategory,
    CostCategoryCreateBody,
    CostCreateBody,
)
from src.infrastructure import Response, ResponseMulti, database

router = APIRouter(prefix="/costs", tags=["Costs"])


@router.get("/categories", status_code=status.HTTP_200_OK)
async def cost_categories(
    _=Depends(op.authorize),
) -> ResponseMulti[CostCategory]:
    """return available cost categories from the database."""

    return ResponseMulti[CostCategory](
        result=[
            CostCategory.model_validate(item)
            async for item in domain.transactions.TransactionRepository().cost_categories()
        ]
    )


@router.post("/categories", status_code=status.HTTP_201_CREATED)
async def cost_category_create(
    _=Depends(op.authorize),
    schema: CostCategoryCreateBody = Body(...),
) -> Response[CostCategory]:
    """create a new cost category."""

    async with database.transaction():
        item: (
            database.CostCategory
        ) = await domain.transactions.TransactionRepository().add_cost_category(
            candidate=database.CostCategory(name=schema.name)
        )

    return Response[CostCategory](result=CostCategory.model_validate(item))


@router.post("", status_code=status.HTTP_201_CREATED)
async def cost_create(body: CostCreateBody = Body(...)) -> Response[Cost]:
    """Create yet another cost."""

    # TODO: get from request after authorization
    user_id = 1

    item: (
        domain.transactions.Cost
    ) = await domain.transactions.TransactionRepository().add_cost(
        candidate=domain.transactions.CostDBCandidate(
            name=body.name,
            value=body.value,
            timestamp=body.timestamp,
            user_id=user_id,
            currency_id=body.currency_id,
            category_id=body.category_id,
        )
    )

    return Response[Cost](result=Cost.model_validate(item))
