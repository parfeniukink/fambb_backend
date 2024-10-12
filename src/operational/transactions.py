import asyncio
from collections.abc import Coroutine
from datetime import date

from src import domain
from src.infrastructure import database, errors


# ==================================================
# costs section
# ==================================================
async def get_costs(
    limit: int,
    offset: int,
    user_id: int | None = None,
) -> tuple[database.Cost, ...]:
    """get paginated costs. proxy values to the repository."""

    items = tuple(
        [
            item
            async for item in domain.transactions.TransactionRepository().costs(
                user_id=user_id, offset=offset, limit=limit
            )
        ]
    )

    return items


async def add_cost(
    name: str,
    value: int,
    timestamp: date,
    currency_id: int,
    category_id: int,
    user_id: int,
) -> database.Cost:

    async with database.transaction() as session:
        tasks = (
            domain.transactions.TransactionRepository().add_cost(
                candidate=database.Cost(
                    name=name,
                    value=value,
                    timestamp=timestamp,
                    user_id=user_id,
                    currency_id=currency_id,
                    category_id=category_id,
                )
            ),
            domain.equity.EquityRepository().decrease_equity(
                currency_id, value
            ),
        )
        instance, *_ = await asyncio.gather(*tasks)
        await session.flush()

    return await domain.transactions.TransactionRepository().cost(
        id_=instance.id
    )


async def update_cost(cost_id: int, **values) -> database.Cost:
    """update the cost with additional validations.

    params:
        ``cost_id``  stands for the candidate identifier
        ``values``  includes update payload candidate

    workflow:
        get cost instance or 404
        if value is the same - remove it from the payload.
        update the ``cost``
        update ``equity``
    """

    duplicates = set()
    transaction_repository = domain.transactions.TransactionRepository()
    equity_repository = domain.equity.EquityRepository()
    cost = await transaction_repository.cost(id_=cost_id)

    for attr, value in values.items():
        try:
            if getattr(cost, attr) == value:
                duplicates.add(attr)
        except AttributeError as error:
            raise errors.DatabaseError(
                f"'costs' table does not have '{attr}' column"
            ) from error

    for attr in duplicates:
        del values[attr]

    tasks: list[Coroutine] = [
        transaction_repository.update_cost(cost, **values),
    ]

    # add tasks depending on ``currency_id`` and ``value`` input parameters
    if (new_currency_id := values.get("currency_id")) is not None:
        if (value := values.get("value")) is not None:
            tasks.append(
                equity_repository.increase_equity(cost.currency.id, cost.value)
            )
            tasks.append(
                equity_repository.decrease_equity(new_currency_id, value)
            )
        else:
            tasks.append(
                equity_repository.increase_equity(cost.currency.id, cost.value)
            )
            tasks.append(
                equity_repository.decrease_equity(new_currency_id, cost.value)
            )
    else:
        if (value := values.get("value")) is not None:
            tasks.append(
                equity_repository.decrease_equity(
                    cost.currency_id, value - cost.value
                )
            )

    async with database.transaction():
        await asyncio.gather(*tasks)

    return cost


async def delete_cost(cost_id: int) -> None:
    """update the cost with additional validations.

    params:
        ``cost_id``  stands for the candidate identifier

    workflow:
        get cost instance or 404
        delete the ``cost``
        increase the ``equity``
    """

    cost = await domain.transactions.TransactionRepository().cost(id_=cost_id)

    tasks = (
        domain.transactions.TransactionRepository().delete(
            database.Cost, candidate_id=cost_id
        ),
        domain.equity.EquityRepository().increase_equity(
            cost.currency_id, cost.value
        ),
    )

    async with database.transaction():
        await asyncio.gather(*tasks)


# ==================================================
# incomes section
# ==================================================
async def get_incomes(
    limit: int,
    offset: int,
    user_id: int | None = None,
) -> tuple[database.Income, ...]:
    """get paginated incomes. proxy values to the repository."""

    items = tuple(
        [
            item
            async for item in domain.transactions.TransactionRepository().incomes(
                user_id=user_id, offset=offset, limit=limit
            )
        ]
    )

    return items


async def add_income(
    name: str,
    value: int,
    timestamp: date,
    source: domain.transactions.IncomeSource,
    currency_id: int,
    user_id: int,
) -> database.Income:
    """add another yet income and change the currency equity."""

    async with database.transaction() as session:
        tasks = (
            domain.transactions.TransactionRepository().add_income(
                candidate=database.Income(
                    name=name,
                    value=value,
                    timestamp=timestamp,
                    source=source,
                    currency_id=currency_id,
                    user_id=user_id,
                )
            ),
            domain.equity.EquityRepository().increase_equity(
                currency_id, value
            ),
        )
        instance, *_ = await asyncio.gather(*tasks)
        await session.flush()

    return await domain.transactions.TransactionRepository().income(
        id_=instance.id
    )


async def update_income(income_id: int, **values) -> database.Income:
    """update the income with additional validations.

    params:
        ``income_id``  stands for the candidate identifier
        ``values``  includes update payload candidate

    workflow:
        get income instance or 404
        if value is the same - remove it from the payload.
        update the ``income``
        update ``equity``
    """

    duplicates = set()
    transaction_repository = domain.transactions.TransactionRepository()
    equity_repository = domain.equity.EquityRepository()
    income = await transaction_repository.income(id_=income_id)

    for attr, value in values.items():
        try:
            if getattr(income, attr) == value:
                duplicates.add(attr)
        except AttributeError as error:
            raise errors.DatabaseError(
                f"'incomes' table does not have '{attr}' column"
            ) from error

    for attr in duplicates:
        del values[attr]

    tasks: list[Coroutine] = [
        transaction_repository.update_income(income, **values),
    ]

    # add tasks depending on ``currency_id`` and ``value`` input parameters
    if (new_currency_id := values.get("currency_id")) is not None:
        tasks.append(
            equity_repository.decrease_equity(income.currency.id, income.value)
        )
        if (value := values.get("value")) is not None:
            tasks.append(
                equity_repository.increase_equity(new_currency_id, value)
            )
        else:
            tasks.append(
                equity_repository.increase_equity(
                    new_currency_id, income.value
                )
            )
    else:
        if (value := values.get("value")) is not None:
            tasks.append(
                equity_repository.increase_equity(
                    income.currency_id, value - income.value
                )
            )

    async with database.transaction():
        await asyncio.gather(*tasks)

    return income


async def delete_income(income_id: int):
    """update the income with additional validations.

    params:
        ``income_id``  stands for the candidate identifier

    workflow:
        get income instance or 404
        delete the ``income``
        decrease ``equity``
    """

    income = await domain.transactions.TransactionRepository().income(
        id_=income_id
    )

    tasks = (
        domain.transactions.TransactionRepository().delete(
            database.Income, candidate_id=income_id
        ),
        domain.equity.EquityRepository().decrease_equity(
            income.currency_id, income.value
        ),
    )

    async with database.transaction():
        await asyncio.gather(*tasks)


# ==================================================
# exchange section
# ==================================================
async def get_currency_exchanges(
    limit: int,
    offset: int,
    user_id: int | None = None,
) -> tuple[database.Exchange, ...]:
    """get paginated costs. proxy values to the repository."""

    items = tuple(
        [
            item
            async for item in domain.transactions.TransactionRepository().exchanges(
                user_id=user_id, offset=offset, limit=limit
            )
        ]
    )

    return items


async def currency_exchange(
    from_value: int,
    to_value: int,
    timestamp: date,
    from_currency_id: int,
    to_currency_id: int,
    user_id: int,
) -> database.Exchange:
    """exchange the currency.

    params:
        ``from_value``  how much you give
        ``to_value``  how much you receive
        ``from_currency_id``  source currency id
        ``to_currency_id``  destination currency id

    workflow:
        create an exchange rate database record
        update equity for both currencies
    """

    async with database.transaction() as session:
        tasks = (
            domain.transactions.TransactionRepository().add_exchange(
                candidate=database.Exchange(
                    to_value=from_value,
                    from_value=to_value,
                    timestamp=timestamp,
                    from_currency_id=from_currency_id,
                    to_currency_id=to_currency_id,
                    user_id=user_id,
                )
            ),
            domain.equity.EquityRepository().decrease_equity(
                currency_id=from_currency_id, value=from_value
            ),
            domain.equity.EquityRepository().increase_equity(
                currency_id=to_currency_id, value=to_value
            ),
        )

        instance, *_ = await asyncio.gather(*tasks)
        await session.flush()

    return await domain.transactions.TransactionRepository().exchange(
        id_=instance.id
    )


async def delete_currency_exchange(item_id: int) -> None:
    """update the income with additional validations.

    params:
        ``item_id``  stands for the candidate identifier

    workflow:
        get item or 404
        delete item
        updaate equity
    """

    item = await domain.transactions.TransactionRepository().exchange(
        id_=item_id
    )

    tasks = (
        domain.transactions.TransactionRepository().delete(
            database.Exchange, candidate_id=item_id
        ),
        domain.equity.EquityRepository().increase_equity(
            item.from_currency_id, item.from_value
        ),
        domain.equity.EquityRepository().decrease_equity(
            item.to_currency_id, item.to_value
        ),
    )

    async with database.transaction():
        await asyncio.gather(*tasks)
