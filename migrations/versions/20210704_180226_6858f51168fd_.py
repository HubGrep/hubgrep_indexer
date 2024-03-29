"""empty message

Revision ID: 6858f51168fd
Revises: f6ee6d5a8841
Create Date: 2021-07-04 18:02:26.254158

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6858f51168fd'
down_revision = 'f6ee6d5a8841'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('export', sa.Column('repo_count', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('export', 'repo_count')
    # ### end Alembic commands ###
