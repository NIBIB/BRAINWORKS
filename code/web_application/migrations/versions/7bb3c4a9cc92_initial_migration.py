"""
Initial Migration

Revision ID: 7bb3c4a9cc92
Revises: 
Create Date: 2022-03-07 19:03:11.775403

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision = '7bb3c4a9cc92'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('brainworks-users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=True),
    sa.Column('email', sqlalchemy_utils.types.email.EmailType(length=100), nullable=False),
    sa.Column('password', sa.String(length=255), nullable=False),
    sa.Column('company', sa.String(length=100), nullable=False),
    sa.Column('department', sa.String(length=50), nullable=True),
    sa.Column('position', sa.String(length=20), nullable=True),
    sa.Column('phone', sqlalchemy_utils.types.phone_number.PhoneNumberType(length=20), nullable=True),
    sa.Column('country', sqlalchemy_utils.types.country.CountryType(length=2), nullable=False),
    sa.Column('purpose', sa.String(length=200), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('verified', sa.Boolean(), nullable=True),
    sa.Column('last_login', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('brainworks-users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_brainworks-users_email'), ['email'], unique=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('brainworks-users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_brainworks-users_email'))

    op.drop_table('brainworks-users')
    # ### end Alembic commands ###
