"""Add commander to rooms

Revision ID: 960957b4f2ec
Revises: 7d6a7a0c6c1d
Create Date: 2016-12-31 08:01:13.453088

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '960957b4f2ec'
down_revision = '7d6a7a0c6c1d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("rooms", sa.Column("commander", sa.String(255), nullable = False))


def downgrade():
    op.drop_column("rooms", "commander")
