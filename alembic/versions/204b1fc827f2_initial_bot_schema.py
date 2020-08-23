"""Initial bot schema

Revision ID: 204b1fc827f2
Revises: 
Create Date: 2020-08-23 20:09:25.569376

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '204b1fc827f2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('admin_actions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('guild_id', sa.Integer(), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=True),
    sa.Column('subject_id', sa.Integer(), nullable=True),
    sa.Column('action_type', sa.Enum('STRIKE', 'TEMP_BAN', 'PERMA_BAN', 'MUTE', name='adminaction'), nullable=True),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('expires_at', sa.DateTime(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('guilds',
    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('admin_actions_enabled', sa.Boolean(), nullable=True),
    sa.Column('subscribers_enabled', sa.Boolean(), nullable=True),
    sa.Column('subscriber_role_id', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('channels',
    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('guild_id', sa.Integer(), nullable=True),
    sa.Column('channel_type', sa.Enum('ADMIN', 'CCIAA', 'ANNOUNCEMENT', 'LOG', name='channeltype'), nullable=True),
    sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('role_control_messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('message_id', sa.Integer(), nullable=True),
    sa.Column('guild_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('subscribers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('guild_id', sa.Integer(), nullable=True),
    sa.Column('subject_id', sa.Integer(), nullable=True),
    sa.Column('once', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('subscribers')
    op.drop_table('role_control_messages')
    op.drop_table('channels')
    op.drop_table('guilds')
    op.drop_table('admin_actions')
    # ### end Alembic commands ###
