"""Add table storages

Revision ID: fd844d630d49
Revises: 2bb97229fe36
Create Date: 2019-10-01 00:06:35.657495

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'ff844d630d49'
down_revision = '3d014d45493f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('schedule_jobs', sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
                    sa.Column('volume_id', sa.String(length=50), nullable=False, unique=True),
                    sa.Column('retention', sa.Integer(), nullable=False, default=5),
                    sa.Column('name', sa.String(length=100), nullable=True),
                    sa.Column('days_of_week', sa.String(length=50), nullable=False),
                    sa.Column('start_time', sa.Integer(), nullable=False),
                    sa.Column('mode', sa.String(length=10), nullable=False),  # Mode SNAPSHOT or BACKUP
                    sa.Column('compression', sa.String(length=20), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=False),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.Column('deleted', sa.Boolean(), nullable=True),
                    sa.Column('deleted_at', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('id', name=op.f('pk_schedule_jobs')))

    with op.batch_alter_table('schedule_jobs', schema=None) as batch_op:
        batch_op.create_foreign_key(batch_op.f('fk_schedule_jobs_storage_id_storages'),
                                    'storages', ['storage_id'], ['id'])


def downgrade():
    pass
