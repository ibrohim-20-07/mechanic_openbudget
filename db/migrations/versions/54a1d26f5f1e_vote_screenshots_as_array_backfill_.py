"""vote screenshots as array, backfill reward amount

Revision ID: 54a1d26f5f1e
Revises: 39aba88ab7db
Create Date: 2026-08-21 16:31:26.029265

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '54a1d26f5f1e'
down_revision: Union[str, Sequence[str], None] = '39aba88ab7db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "votes",
        sa.Column("screenshot_file_ids", postgresql.ARRAY(sa.String()), nullable=True),
    )
    op.execute("UPDATE votes SET screenshot_file_ids = ARRAY[screenshot_file_id]")
    op.alter_column("votes", "screenshot_file_ids", nullable=False)
    op.drop_column("votes", "screenshot_file_id")

    # reward_amount is now locked in at submission time instead of confirmation time;
    # backfill any still-pending votes that predate this change using the current
    # vote_price setting (accurate here since the price hasn't changed since they were submitted)
    op.execute(
        """
        UPDATE votes
        SET reward_amount = (SELECT value::numeric FROM global_settings WHERE key = 'vote_price')
        WHERE status = 'PENDING' AND reward_amount IS NULL
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column("votes", sa.Column("screenshot_file_id", sa.String(), nullable=True))
    op.execute("UPDATE votes SET screenshot_file_id = screenshot_file_ids[1]")
    op.alter_column("votes", "screenshot_file_id", nullable=False)
    op.drop_column("votes", "screenshot_file_ids")
