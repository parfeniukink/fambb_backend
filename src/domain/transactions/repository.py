import itertools
from collections.abc import AsyncGenerator

from tests.mock_storage import Storage

from src.domain.finances import Currency

from .entities import (
    Cost,
    CostCateogoryFlat,
    CostDBCandidate,
    Exchange,
    Income,
    OperationType,
    Transaction,
)


class TransactionRepository:
    """
    TransactionRepository is a data access entrypoint.
    It allows manage costs, incomes, exchanges.
    Everything that could be treated as a 'Money Transaction'.

    It uses the 'Query Builder' to create SQL queries.
    """

    async def filter(
        self,
        operation: OperationType | None,
        currency_id: int | None = None,
        limit: int | None = None,
    ) -> AsyncGenerator[Transaction, None]:
        """
        Params:
            ``operations`` - if set to ``None`` then all types of a transaction
                will be returned.

            ``limit`` - limit output results

        """

        # TODO: build the SQL query base on ``operation``.
        """sql
        SELECT (transaction fields) FROM costs
        WHERE (**filters)
        ORDER BY ``timestamp``
        """

        costs: list[Cost] = [
            Cost(
                **item,
                currency=Currency(**Storage.currencies[item["currency_id"]]),
                category=CostCateogoryFlat(
                    **Storage.cost_categories[item["category_id"]]
                ),
            )
            for item in Storage.costs.values()
        ]
        incomes: list[Income] = [
            Income(
                **item,
                currency=Currency(**Storage.currencies[item["currency_id"]]),
            )
            for item in Storage.incomes.values()
        ]
        exchanges: list[Exchange] = [
            Exchange(
                **item,
                to_currency=Currency(
                    **Storage.currencies[item["to_currency_id"]]
                ),
                from_currency=Currency(
                    **Storage.currencies[item["from_currency_id"]]
                ),
            )
            for item in Storage.exchange.values()
        ]

        # TODO: Remove after SQL LIMIT is added
        items_count = 0

        for item in itertools.chain(costs, incomes, exchanges):
            name = (
                item.name
                if isinstance(item, (Income, Cost))
                else "Currency Exchange"
            )

            if isinstance(item, (Income, Cost)):
                item_currency_id = item.currency.id
            else:
                item_currency_id = item.to_currency.id

            if operation is not None:
                _operation = operation
            else:
                if isinstance(item, Income):
                    _operation = "income"
                elif isinstance(item, Cost):
                    _operation = "cost"
                elif isinstance(item, Exchange):
                    _operation = "exchange"
                else:
                    raise Exception(f"Operation {operation} is not available")

            # NOTE: The code-level implementation of a filteration
            # TODO: Removed after SQL LIMIT is added
            if currency_id is not None and currency_id != item_currency_id:
                # skip if a specified value is not in the results
                continue

            if limit is not None and items_count > limit:
                # break if out of the limit
                return

            yield Transaction(
                name=name,
                value=item.value,
                currency=(
                    item.currency
                    if isinstance(item, (Cost, Income))
                    else item.to_currency
                ),
                operation=_operation,
            )

    async def cost_categories(self) -> AsyncGenerator[CostCateogoryFlat, None]:
        for item in Storage.cost_categories.values():
            yield item

    async def add_cost_category(self, name: str) -> CostCateogoryFlat:
        # TODO: move this validation to the DB level
        for item in Storage.cost_categories.values():
            if item.name == name:
                raise Exception("This Cost category already exist")

        new_id = max(Storage.cost_categories.keys())
        item = CostCateogoryFlat(id=new_id, name=name)

        Storage.cost_categories[new_id] = item

        return item

    async def add_cost(self, candidate: CostDBCandidate) -> Cost:
        new_id = max(Storage.costs.keys()) + 1
        instance: dict = dict(
            id=new_id,
            name=candidate.name,
            value=candidate.value,
            timestamp=candidate.timestamp,
            user_id=candidate.user_id,
            currency_id=candidate.currency_id,
            category_id=candidate.category_id,
        )

        Storage.costs[new_id] = instance

        return Cost(
            **instance,
            currency=Currency(**Storage.currencies[instance["currency_id"]]),
            category=CostCateogoryFlat(
                **Storage.cost_categories[instance["category_id"]]
            ),
        )
