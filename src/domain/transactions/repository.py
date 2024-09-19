import itertools
from collections.abc import AsyncGenerator
from datetime import datetime

from src.domain.finances import Currency

from .entities import (
    Cost,
    CostCateogoryFlat,
    CostFlat,
    Currency,
    Exchange,
    Income,
    IncomeFlat,
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

    usd = Currency(id=1, name="USD", sign="$")
    uah = Currency(id=2, name="UAH", sign="#")

    _mock_transactions: dict[OperationType, list] = {
        "cost": [
            Cost(
                id=1,
                name="Test cost 1",
                value=100_00,
                timestamp=datetime.now(),
                user_id=1,
                currency=usd,
                category=CostCateogoryFlat(id=1, name="Test category 1"),
            ),
            Cost(
                id=2,
                name="Test cost 2",
                value=100_00,
                timestamp=datetime.now(),
                user_id=1,
                currency=uah,
                category=CostCateogoryFlat(id=2, name="Test category 2"),
            ),
            Cost(
                id=3,
                name="Test cost 3",
                value=100_00,
                timestamp=datetime.now(),
                user_id=1,
                currency=usd,
                category=CostCateogoryFlat(id=1, name="Test category 1"),
            ),
        ],
        "income": [
            Income(
                id=1,
                value=20000,
                name="Test Income 1",
                source="revenue",
                timestamp=datetime.now(),
                user_id=1,
                currency=uah,
            ),
            Income(
                id=2,
                value=22000,
                name="Test Income 2",
                source="other",
                timestamp=datetime.now(),
                user_id=1,
                currency=usd,
            ),
        ],
        "exchange": [
            Exchange(
                id=1,
                value=230000,
                timestamp=datetime.now(),
                user_id=1,
                from_currency=uah,
                to_currency=usd,
            ),
        ],
    }
    _mock_cost_categories = [
        CostCateogoryFlat(id=1, name="Food"),
        CostCateogoryFlat(id=2, name="Services"),
        CostCateogoryFlat(id=3, name="House"),
        CostCateogoryFlat(id=4, name="Sport"),
        CostCateogoryFlat(id=5, name="Education"),
    ]

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

        costs: list[Cost] = self._mock_transactions["cost"]
        incomes: list[Income] = self._mock_transactions["income"]
        exchanges: list[Exchange] = self._mock_transactions["exchange"]

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
        for item in self._mock_cost_categories:
            yield item

    async def add_cost_category(self, name: str) -> CostCateogoryFlat:
        # TODO: move this validation to the DB level
        for item in TransactionRepository._mock_cost_categories:
            if item.name == name:
                raise Exception("This Cost category already exist")

        item = CostCateogoryFlat(
            id=TransactionRepository._mock_cost_categories[-1].id + 1,
            name=name,
        )
        TransactionRepository._mock_cost_categories.append(item)

        return item
