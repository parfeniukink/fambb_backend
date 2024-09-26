"""
This is the Application (Operational) layer that could be treated
as a bridge between the Presentation layer and the rest of the application.

It basically represents all the operations in the whole application on
the top level.

Each component in this layer defines specific operations that are
allowed to be performed by the user of this system in general.
"""

__all__ = (
    "authorize",
    "get_last_transactions",
    "get_transactions",
    "user_retrieve",
)


from .authorization import authorize
from .transactions import get_last_transactions, get_transactions
from .users import user_retrieve
