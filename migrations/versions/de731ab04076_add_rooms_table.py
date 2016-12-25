"""Add rooms table

Revision ID: de731ab04076
Revises:
Create Date: 2016-12-25 15:36:51.183693

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'de731ab04076'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("rooms",
        sa.Column("room_id", sa.String(255), primary_key = True, unique = True),
        sa.Column("room_type", sa.Integer, nullable = False)
    )

    op.create_index("rooms_room_ids", "rooms", ["room_id"])
    op.create_index("rooms_room_type", "rooms", ["room_type"])


def downgrade():
    op.drop_index("rooms_room_ids", "rooms")
    op.drop_index("rooms_room_type", "rooms")

    op.drop_table("rooms")

