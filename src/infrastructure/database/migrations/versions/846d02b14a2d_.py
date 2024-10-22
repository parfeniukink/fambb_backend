"""empty message

Revision ID: 846d02b14a2d
Revises: 3ba9fbfef1fa
Create Date: 2024-10-22 16:24:03.019529

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "846d02b14a2d"
down_revision: Union[str, None] = "3ba9fbfef1fa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("users", "common_costs")
    op.drop_column("users", "common_incomes")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "users",
        sa.Column(
            "common_incomes", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "common_costs", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    # ### end Alembic commands ###
