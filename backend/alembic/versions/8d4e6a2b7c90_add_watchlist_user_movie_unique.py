"""add watchlist user/movie uniqueness

Revision ID: 8d4e6a2b7c90
Revises: 7c2f9f1b6a41
Create Date: 2026-09-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "8d4e6a2b7c90"

down_revision: Union[str, Sequence[str], None] = "a0730e6d8cc6"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint("uq_watchlist_user_movie", "watchlist", ["user_id", "movie_id"])


def downgrade() -> None:
    op.drop_constraint("uq_watchlist_user_movie", "watchlist", type_="unique")