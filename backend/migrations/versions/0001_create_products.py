"""Create products catalog table."""

import sqlalchemy as sa
from alembic import op

revision = "0001_create_products"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("category", sa.String(length=256)),
        sa.Column("price", sa.Numeric(12, 2)),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("image_path", sa.Text(), nullable=False),
        sa.Column("image_sha256", sa.String(length=64), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("products")
