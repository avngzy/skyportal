"""Test migration

Revision ID: f9611048498a
Revises: f7c1e785d7a4
Create Date: 2022-01-14 19:04:39.250447

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f9611048498a'
down_revision = 'f7c1e785d7a4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('galaxys', sa.Column('magk', sa.Float(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('galaxys', 'magk')
    # ### end Alembic commands ###
