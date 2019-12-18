"""Added experiment_measurements table

Revision ID: 31cb73361b6f
Revises: 64f0cb642938
Create Date: 2019-12-07 19:05:07.519908

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "31cb73361b6f"
down_revision = "64f0cb642938"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "experiment_measurements",
        sa.Column("experiment_id", sa.Integer),
        sa.Column("top_parent_id", sa.Integer, sa.ForeignKey("samples.id")),
        sa.Column(
            "sample_id",
            sa.Integer,
            sa.ForeignKey("samples.id"),
            primary_key=True
        ),
    )


def downgrade():
    op.drop_table("experiment_measurements")
