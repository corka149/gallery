"""rename category to category

Revision ID: 34aa2cc482b1
Revises: 46aee3cb88f0
Create Date: 2025-04-10 20:24:36.399084

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '34aa2cc482b1'
down_revision: Union[str, None] = '46aee3cb88f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename 'tags' column to 'category' in 'image' table
    with op.batch_alter_table('image') as batch_op:
        batch_op.alter_column('tags', new_column_name='category')
        batch_op.create_index('ix_image_category', ['category'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Rename 'category' column back to 'tags' in 'image' table
    with op.batch_alter_table('image') as batch_op:
        batch_op.alter_column('category', new_column_name='tags')
