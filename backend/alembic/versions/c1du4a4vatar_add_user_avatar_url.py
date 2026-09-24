"""add user avatar_url for cloudinary

Revision ID: c1du4a4vatar
Revises: 86602e248367
Create Date: 2026-09-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1du4a4vatar'
down_revision: Union[str, Sequence[str], None] = '86602e248367'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('avatar_url', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'avatar_url')