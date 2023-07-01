"""Update table storages

Revision ID: ff944d630d49
Revises: ff844d630d49
Create Date: 2020-06-09 00:06:35.657495

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'ff944d630d49'
down_revision = 'ff844d630d49'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('storages', schema=None) as batch_op:
        batch_op.add_column(sa.Column('module', sa.String(20), nullable=False, default='file'))
        batch_op.add_column(sa.Column('configuration', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('disk_used', sa.BigInteger, nullable=True, default=0))
        batch_op.add_column(sa.Column('disk_allowed', sa.BigInteger, nullable=True, default=0))
        batch_op.add_column(sa.Column('created_at', sa.DateTime())),
        batch_op.add_column(sa.Column('updated_at', sa.DateTime())),
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime())),
        batch_op.add_column(sa.Column('deleted', sa.Boolean())),


def downgrade():
    pass
