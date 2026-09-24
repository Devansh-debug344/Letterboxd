"""add cloudinary artwork refs to movies

Revision ID: m0v13img
Revises: c1du4a4vatar
Create Date: 2026-09-24 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'm0v13img'
down_revision: Union[str, Sequence[str], None] = 'c1du4a4vatar'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('movies', sa.Column('poster_public_id', sa.String(), nullable=True))
    op.add_column('movies', sa.Column('backdrop', sa.String(), nullable=True))
    op.add_column('movies', sa.Column('backdrop_public_id', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('movies', 'backdrop_public_id')
    op.drop_column('movies', 'backdrop')
    op.drop_column('movies', 'poster_public_id')