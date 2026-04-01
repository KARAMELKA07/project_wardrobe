"""Add clothing item metadata fields

Revision ID: 8b1f7f3c9c2a
Revises: e93d24105967
Create Date: 2026-03-31 14:10:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8b1f7f3c9c2a"
down_revision = "e93d24105967"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("clothing_items", schema=None) as batch_op:
        batch_op.add_column(sa.Column("fit", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("layer_level", sa.String(length=50), nullable=True))
        batch_op.add_column(
            sa.Column(
                "insulation_rating",
                sa.Float(),
                nullable=False,
                server_default=sa.text("0"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "waterproof",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "windproof",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            )
        )


def downgrade():
    with op.batch_alter_table("clothing_items", schema=None) as batch_op:
        batch_op.drop_column("windproof")
        batch_op.drop_column("waterproof")
        batch_op.drop_column("insulation_rating")
        batch_op.drop_column("layer_level")
        batch_op.drop_column("fit")
