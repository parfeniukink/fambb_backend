"""empty message

Revision ID: ea658b49d015
Revises: 582ba7eac761
Create Date: 2025-03-11 10:58:49.224766

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ea658b49d015"
down_revision: Union[str, None] = "582ba7eac761"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "users",
        sa.Column(
            "show_equity", sa.Boolean(), server_default="f", nullable=False
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("users", "show_equity")
    # ### end Alembic commands ###
