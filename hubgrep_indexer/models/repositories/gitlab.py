from iso8601 import iso8601
import logging

from typing import Dict
from hubgrep_indexer import db
from hubgrep_indexer.models.repositories.abstract_repository import Repository
from sqlalchemy import Index

logger = logging.getLogger(__name__)

""" expected GitLab result
    {
        'id': 1241825,
        'description': 'Pacote LaTeXe para produção de monografias, dissertações e teses',
        'name': 'ufrrj',
        'name_with_namespace': 'Alessandro Duarte / ufrrj',
        'path': 'ufrrj',
        'path_with_namespace': 'dedekindbr/ufrrj',
        'created_at': '2016-05-30T04:27:14.463Z',
        'default_branch': 'master',
        'tag_list': [],
        'ssh_url_to_repo': 'git@gitlab.com:dedekindbr/ufrrj.git',
        'http_url_to_repo': 'https://gitlab.com/dedekindbr/ufrrj.git',
        'web_url': 'https://gitlab.com/dedekindbr/ufrrj',
        'readme_url': 'https://gitlab.com/dedekindbr/ufrrj/-/blob/master/README.md',
        'avatar_url': None,
        'forks_count': 0,
        'star_count': 0,
        'last_activity_at': '2016-05-30T04:27:15.194Z',
        'namespace': {'id': 502506,
                      'name': 'Alessandro Duarte',
                      'path': 'dedekindbr',
                      'kind': 'user',
                      'full_path': 'dedekindbr',
                      'parent_id': None,
                      'avatar_url': 'https://secure.gravatar.com/avatar/ec3a8f5183465a232283493f3de0a80d?s=80&d=identicon',
                      'web_url': 'https://gitlab.com/dedekindbr'}
    }
"""


class GitlabRepository(Repository):
    __tablename__ = "gitlab_repositories"

    gitlab_id = db.Column(db.Integer)  # 'id': 1241825,
    description = db.Column(db.Text)  # 'description': 'Pacote LaTeXe para produção de monografias, dissertações e teses',
    name = db.Column(db.String(500))  # 'name': 'ufrrj',
    name_with_namespace = db.Column(db.String(500))  # 'name_with_namespace': 'Alessandro Duarte / ufrrj',
    path = db.Column(db.String(500))  # 'path': 'ufrrj',
    path_with_namespace = db.Column(db.String(500))  #'path_with_namespace': 'dedekindbr/ufrrj',
    created_at = db.Column(db.DateTime)  # 'created_at': '2016-05-30T04:27:14.463Z',
    last_activity_at = db.Column(db.DateTime)  # 'last_activity_at': '2016-05-30T04:27:15.194Z',  # TODO does this mean updated_at/pushed_at?
    # TODO what about updated_at/pushed_at? can we get this?
    default_branch = db.Column(db.String(500))  # 'default_branch': 'master',
    # tag_list = 'tag_list': [],  # TODO skipping for now, as its not important, and may need more tables
    ssh_url_to_repo = db.Column(db.String(500))  # 'ssh_url_to_repo': 'git@gitlab.com:dedekindbr/ufrrj.git',
    http_url_to_repo = db.Column(db.String(500))  # 'http_url_to_repo': 'https://gitlab.com/dedekindbr/ufrrj.git',
    web_url = db.Column(db.String(500))  # 'web_url': 'https://gitlab.com/dedekindbr/ufrrj',
    readme_url = db.Column(db.String(500))  # 'readme_url': 'https://gitlab.com/dedekindbr/ufrrj/-/blob/master/README.md',
    avatar_url = db.Column(db.String(500))  # 'avatar_url': None,
    forks_count = db.Column(db.String(500))  # 'forks_count': 0,
    star_count = db.Column(db.String(500))  # 'star_count': 0,
    user_name = db.Column(db.String(500))  # TODO do we need more from the following object values?
    """ 
    'namespace': {'id': 502506,
                  'name': 'Alessandro Duarte',
                  'path': 'dedekindbr',
                  'kind': 'user',
                  'full_path': 'dedekindbr',
                  'parent_id': None,
                  'avatar_url': 'https://secure.gravatar.com/avatar/ec3a8f5183465a232283493f3de0a80d?s=80&d=identicon',
                  'web_url': 'https://gitlab.com/dedekindbr'}
    """
    unified_select_statement_template = """
    select
        gitlab_id as foreign_id,
        name as name,
        user_name as username,
        description as description,
        created_at as created_at,
        last_activity_at as updated_at,
        last_activity_at as pushed_at,
        star_count as stars_count,
        forks_count as forks_count,
        false as is_private,
        false as is_fork,
        false as is_archived,
        false as is_disabled,
        false as is_mirror,
        web_url as homepage_url,
        http_url_to_repo as repo_url
    from
        {TABLE_NAME}
    where
        hosting_service_id = {HOSTING_SERVICE_ID}
    """

    @classmethod
    def from_dict(cls, hosting_service_id, d: dict, update=True) -> "GitlabRepository":
        user_name = d['namespace']['path']
        name = d['name']
        gitlab_id = d['id']

        repo = cls()

        repo.hosting_service_id = hosting_service_id
        repo.gitlab_id = gitlab_id
        repo.name = name
        repo.user_name = user_name
        repo.description = d["description"]
        repo.name_with_namespace = d["name_with_namespace"]
        repo.path = d["path"]
        repo.path_with_namespace = d["path_with_namespace"]
        repo.created_at = iso8601.parse_date(d["created_at"])
        repo.last_activity_at = iso8601.parse_date(d["last_activity_at"])
        repo.default_branch = d.get("default_branch", None)
        repo.ssh_url_to_repo = d["ssh_url_to_repo"]
        repo.http_url_to_repo = d["http_url_to_repo"]
        repo.web_url = d["web_url"]
        repo.readme_url = d["readme_url"]
        repo.avatar_url = d["avatar_url"]
        repo.forks_count = d["forks_count"]
        repo.star_count = d["star_count"]

        return repo

    def to_dict(self) -> Dict[str, str]:
        repo = dict()
        repo["hosting_service_id"] = self.hosting_service_id
        repo["gitlab_id"] = self.gitlab_id
        repo["name"] = self.name
        repo["user_name"] = self.user_name
        repo["description"] = self.description
        repo["name_with_namespace"] = self.name_with_namespace
        repo["path"] = self.path
        repo["path_with_namespace"] = self.path_with_namespace
        repo["created_at"] = self.created_at
        repo["last_activity_at"] = self.last_activity_at
        repo["default_branch"] = self.default_branch
        repo["ssh_url_to_repo"] = self.ssh_url_to_repo
        repo["http_url_to_repo"] = self.http_url_to_repo
        repo["web_url"] = self.web_url
        repo["readme_url"] = self.readme_url
        repo["avatar_url"] = self.avatar_url
        repo["forks_count"] = self.forks_count
        repo["star_count"] = self.star_count
        return repo
