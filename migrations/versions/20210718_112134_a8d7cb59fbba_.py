""" Turn hosting_service column "api_key" into a list ("api_keys") - when downgrading, only keeping api_keys[0]!

Revision ID: a8d7cb59fbba
Revises: b387a1d19b85
Create Date: 2021-07-18 11:21:34.832330

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm, text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a8d7cb59fbba'
down_revision = 'b387a1d19b85'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    try:
        op.add_column('hosting_service', sa.Column('api_keys', postgresql.ARRAY(sa.String(length=500))))

        session.execute(text("""
            UPDATE
              hosting_service
            SET
              api_keys[0] = api_key
        """))
        session.commit()

        op.drop_column('hosting_service', 'api_key')

    except Exception as e:
        print("UPGRADE FAILED - ROLLING BACK CHANGES")
        op.drop_column('hosting_service', 'api_keys')
        session.rollback()
        print("CHANGES ROLLED BACK SUCCESSFULLY")
        raise e


def downgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    try:
        op.add_column('hosting_service',
                      sa.Column('api_key', sa.VARCHAR(length=500), autoincrement=False, nullable=True))

        session.execute(text("""
                UPDATE
                  hosting_service
                SET
                  api_key = api_keys[0] 
            """))
        session.commit()

        op.drop_column('hosting_service', 'api_keys')

    except Exception as e:
        print("UPGRADE FAILED - ROLLING BACK CHANGES")
        op.drop_column('hosting_service', 'api_key')
        session.rollback()
        print("CHANGES ROLLED BACK SUCCESSFULLY")
        raise e
