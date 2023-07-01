"""Add table storages

Revision ID: fd844d630d49
Revises: 2bb97229fe36
Create Date: 2019-10-01 00:06:35.657495

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'ff964d630d49'
down_revision = 'ff954d630d49'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('nodes', sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
                    sa.Column('name', sa.String(length=100), nullable=False),
                    sa.Column('host', sa.String(length=100), nullable=True),
                    sa.Column('port', sa.Integer(), nullable=False, default=50051),
                    sa.Column('created_at', sa.DateTime(), nullable=False),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.Column('deleted', sa.Boolean(), nullable=True),
                    sa.Column('deleted_at', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('id', name=op.f('pk_nodes')))

    with op.batch_alter_table('storages', schema=None) as batch_op:
        batch_op.create_foreign_key(batch_op.f('fk_storages_node_id_nodes'),
                                    'nodes', ['node_id'], ['id'])


def downgrade():
    pass
