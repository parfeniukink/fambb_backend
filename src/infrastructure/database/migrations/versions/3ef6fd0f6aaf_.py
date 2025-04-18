"""empty message

Revision ID: 3ef6fd0f6aaf
Revises: 79a0d6d194ca
Create Date: 2024-12-03 21:51:31.388131

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "3ef6fd0f6aaf"
down_revision: Union[str, None] = "79a0d6d194ca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "users",
        "cost_snippets",
        existing_type=postgresql.ARRAY(sa.INTEGER()),
        type_=postgresql.ARRAY(sa.String(), dimensions=1),
        existing_nullable=True,
    )
    op.alter_column(
        "users",
        "income_snippets",
        existing_type=postgresql.ARRAY(sa.INTEGER()),
        type_=postgresql.ARRAY(sa.String(), dimensions=1),
        existing_nullable=True,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "users",
        "income_snippets",
        existing_type=postgresql.ARRAY(sa.String(), dimensions=1),
        type_=postgresql.ARRAY(sa.INTEGER()),
        existing_nullable=True,
    )
    op.alter_column(
        "users",
        "cost_snippets",
        existing_type=postgresql.ARRAY(sa.String(), dimensions=1),
        type_=postgresql.ARRAY(sa.INTEGER()),
        existing_nullable=True,
    )
    # ### end Alembic commands ###
