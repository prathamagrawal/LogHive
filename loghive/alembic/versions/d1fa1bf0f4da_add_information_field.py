"""Add information field

Revision ID: d1fa1bf0f4da
Revises: abd7228d3b72
Create Date: 2024-12-08 21:59:02.182315

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d1fa1bf0f4da"
down_revision: Union[str, None] = "abd7228d3b72"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "logging_details",
        sa.Column("information", sa.String(), nullable=True),
        schema="logs",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("logging_details", "information", schema="logs")
    # ### end Alembic commands ###
