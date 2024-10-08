"""Add youtube_chat_message_cursors table.

Revision ID: 188d5b9df211
Revises: 935a522dc2e9
Create Date: 2024-06-21 13:12:35.923971

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "188d5b9df211"
down_revision = "935a522dc2e9"
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "youtube_chat_message_cursors",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("video_id", sa.String(), nullable=False),
        sa.Column("message_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["youtube_chat_messages.message_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("video_id", "message_id", name="unique_video_message"),
    )
    # ### end Alembic commands ###


def downgrade():
    """Downgrade."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("youtube_chat_message_cursors")
    # ### end Alembic commands ###
