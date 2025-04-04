"""Add reset token fields to User model

Revision ID: a96afab5d252
Revises: 
Create Date: 2025-04-03 01:29:45.312280

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a96afab5d252'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reset_token', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('reset_token_expiry', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('reset_token_expiry')
        batch_op.drop_column('reset_token')

    # ### end Alembic commands ###
