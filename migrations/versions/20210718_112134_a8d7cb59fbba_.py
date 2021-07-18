""" Turn hosting_service column "api_key" into a list ("api_keys") - deleted all hosters, re-import!

Revision ID: a8d7cb59fbba
Revises: b387a1d19b85
Create Date: 2021-07-18 11:21:34.832330

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.dialects import postgresql
from hubgrep_indexer.models.hosting_service import HostingService

# revision identifiers, used by Alembic.
revision = 'a8d7cb59fbba'
down_revision = 'b387a1d19b85'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('hosting_service', sa.Column('api_keys', postgresql.ARRAY(sa.String(length=500))))
    op.drop_column('hosting_service', 'api_key')
    # ### end Alembic commands ###

    bind = op.get_bind()
    session = orm.Session(bind=bind)

    deleted = session.query(HostingService).delete()
    print("hosting_services deleted:", deleted)
    print("you should manually re-import hosting_services to populate api_keys correctly!")
    session.commit()


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('hosting_service', sa.Column('api_key', sa.VARCHAR(length=500), autoincrement=False, nullable=True))
    op.drop_column('hosting_service', 'api_keys')
    # ### end Alembic commands ###
