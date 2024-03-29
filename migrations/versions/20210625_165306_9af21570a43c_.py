"""empty message

Revision ID: 9af21570a43c
Revises: ce2939d5eaf0
Create Date: 2021-06-25 16:53:06.998190

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9af21570a43c'
down_revision = 'ce2939d5eaf0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('gitea_repository',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('hosting_service_id', sa.Integer(), nullable=False),
    sa.Column('gitea_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=200), nullable=True),
    sa.Column('owner_username', sa.String(length=200), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('empty', sa.Boolean(), nullable=True),
    sa.Column('private', sa.Boolean(), nullable=True),
    sa.Column('fork', sa.Boolean(), nullable=True),
    sa.Column('mirror', sa.Boolean(), nullable=True),
    sa.Column('size', sa.Integer(), nullable=True),
    sa.Column('website', sa.String(length=200), nullable=True),
    sa.Column('stars_count', sa.Integer(), nullable=True),
    sa.Column('forks_count', sa.String(length=200), nullable=True),
    sa.Column('watchers_count', sa.Integer(), nullable=True),
    sa.Column('open_issues_count', sa.Integer(), nullable=True),
    sa.Column('default_branch', sa.String(length=200), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('pushed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['hosting_service_id'], ['hosting_service.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('gitlab_repository',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('hosting_service_id', sa.Integer(), nullable=False),
    sa.Column('gitlab_id', sa.Integer(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('name', sa.String(length=200), nullable=True),
    sa.Column('name_with_namespace', sa.String(length=200), nullable=True),
    sa.Column('path', sa.String(length=200), nullable=True),
    sa.Column('path_with_namespace', sa.String(length=200), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('last_activity_at', sa.DateTime(), nullable=True),
    sa.Column('default_branch', sa.String(length=200), nullable=True),
    sa.Column('ssh_url_to_repo', sa.String(length=200), nullable=True),
    sa.Column('http_url_to_repo', sa.String(length=200), nullable=True),
    sa.Column('web_url', sa.String(length=200), nullable=True),
    sa.Column('readme_url', sa.String(length=200), nullable=True),
    sa.Column('avatar_url', sa.String(length=200), nullable=True),
    sa.Column('forks_count', sa.String(length=200), nullable=True),
    sa.Column('star_count', sa.String(length=200), nullable=True),
    sa.Column('user_name', sa.String(length=200), nullable=True),
    sa.ForeignKeyConstraint(['hosting_service_id'], ['hosting_service.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('github_repository', sa.Column('fork_count', sa.Integer(), nullable=True))
    op.add_column('github_repository', sa.Column('hosting_service_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'github_repository', 'hosting_service', ['hosting_service_id'], ['id'])
    op.drop_column('github_repository', 'fork_coung')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('github_repository', sa.Column('fork_coung', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'github_repository', type_='foreignkey')
    op.drop_column('github_repository', 'hosting_service_id')
    op.drop_column('github_repository', 'fork_count')
    op.drop_table('gitlab_repository')
    op.drop_table('gitea_repository')
    # ### end Alembic commands ###
