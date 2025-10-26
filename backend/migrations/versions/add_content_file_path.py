"""
Migration script to add the `content_file_path` column to the `generated_content` table.
"""

from alembic import op
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = 'add_content_file_path'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Apply the migration: add `content_file_path` column."""
    op.add_column('generated_content', sa.Column('content_file_path', sa.String(), nullable=True))

def downgrade():
    """Revert the migration: remove `content_file_path` column."""
    op.drop_column('generated_content', 'content_file_path')
