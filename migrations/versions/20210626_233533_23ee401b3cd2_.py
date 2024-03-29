"""empty message

Revision ID: 23ee401b3cd2
Revises: 99c1c5ca9c91
Create Date: 2021-06-26 23:35:33.145927

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '23ee401b3cd2'
down_revision = '99c1c5ca9c91'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('gitlab_repository', 'avatar_url',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=500),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'default_branch',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=500),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'forks_count',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=500),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'http_url_to_repo',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=500),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'name',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=500),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'name_with_namespace',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=500),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'path',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=500),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'path_with_namespace',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=500),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'readme_url',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=500),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'ssh_url_to_repo',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=500),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'star_count',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=500),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'user_name',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=500),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'web_url',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=500),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('gitlab_repository', 'web_url',
               existing_type=sa.String(length=500),
               type_=sa.VARCHAR(length=200),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'user_name',
               existing_type=sa.String(length=500),
               type_=sa.VARCHAR(length=200),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'star_count',
               existing_type=sa.String(length=500),
               type_=sa.VARCHAR(length=200),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'ssh_url_to_repo',
               existing_type=sa.String(length=500),
               type_=sa.VARCHAR(length=200),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'readme_url',
               existing_type=sa.String(length=500),
               type_=sa.VARCHAR(length=200),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'path_with_namespace',
               existing_type=sa.String(length=500),
               type_=sa.VARCHAR(length=200),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'path',
               existing_type=sa.String(length=500),
               type_=sa.VARCHAR(length=200),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'name_with_namespace',
               existing_type=sa.String(length=500),
               type_=sa.VARCHAR(length=200),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'name',
               existing_type=sa.String(length=500),
               type_=sa.VARCHAR(length=200),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'http_url_to_repo',
               existing_type=sa.String(length=500),
               type_=sa.VARCHAR(length=200),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'forks_count',
               existing_type=sa.String(length=500),
               type_=sa.VARCHAR(length=200),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'default_branch',
               existing_type=sa.String(length=500),
               type_=sa.VARCHAR(length=200),
               existing_nullable=True)
    op.alter_column('gitlab_repository', 'avatar_url',
               existing_type=sa.String(length=500),
               type_=sa.VARCHAR(length=200),
               existing_nullable=True)
    # ### end Alembic commands ###
