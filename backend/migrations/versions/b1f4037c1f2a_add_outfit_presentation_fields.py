"""Add saved outfit board fields

Revision ID: b7cf5f8d4a31
Revises: 8b1f7f3c9c2a
Create Date: 2026-03-31 18:20:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b7cf5f8d4a31"
down_revision = "8b1f7f3c9c2a"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("outfits", schema=None) as batch_op:
        batch_op.add_column(sa.Column("feature_scores", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("reasons", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("user_photo_url", sa.String(length=500), nullable=True))


def downgrade():
    with op.batch_alter_table("outfits", schema=None) as batch_op:
        batch_op.drop_column("user_photo_url")
        batch_op.drop_column("reasons")
        batch_op.drop_column("feature_scores")
