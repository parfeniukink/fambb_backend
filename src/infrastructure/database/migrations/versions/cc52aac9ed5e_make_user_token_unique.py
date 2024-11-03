"""make user token unique

Revision ID: cc52aac9ed5e
Revises: e787ed8f47cb
Create Date: 2024-10-29 16:37:26.039296

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cc52aac9ed5e"
down_revision: Union[str, None] = "e787ed8f47cb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(op.f("uq_users_token"), "users", ["token"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f("uq_users_token"), "users", type_="unique")
    # ### end Alembic commands ###
