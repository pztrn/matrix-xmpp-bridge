"""Add rooms_types table

Revision ID: 7d6a7a0c6c1d
Revises: de731ab04076
Create Date: 2016-12-26 22:19:25.156107

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7d6a7a0c6c1d'
down_revision = 'de731ab04076'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("rooms_types",
        sa.Column("id", sa.Integer, primary_key = True, unique = True, autoincrement = True),
        sa.Column("name", sa.String(255), nullable = False),
        sa.Column("description", sa.String(255), nullable = False)
    )

    op.execute("INSERT INTO rooms_types (name, description) VALUES ('Command room', 'Command room is a private room for setting up a bridge between other room and XMPP MUC')")
    op.execute("INSERT INTO rooms_types (name, description) VALUES ('Bridged room', 'Bridged room is a public room which have operating bridge between it and XMPP MUC. Most of commands unavailable here.')")


def downgrade():
    op.drop_table("rooms_types")
