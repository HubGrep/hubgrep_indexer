from typing import Dict
from iso8601 import iso8601

from hubgrep_indexer import db
from hubgrep_indexer.models.repositories.abstract_repository import Repository

from sqlalchemy import Index

"""
    {'id': 2,
    'owner': {'id': 5,
              'login': 'codi.cooperatiu',
              'full_name': '',
              'email': '',
              'avatar_url': 'http://gitea.codi.coop/avatars/a89a876bb0456b115c77dbee684d409b',
              'username': 'codi.cooperatiu'},
    'name': 'codi-theme',
    'full_name': 'codi.cooperatiu/codi-theme',
    'description': '',
    'empty': False,
    'private': False,
    'fork': False,
    'parent': None,
    'mirror': False,
    'size': 5188,
    'html_url': 'http://gitea.codi.coop/codi.cooperatiu/codi-theme',
    'ssh_url': 'root@gitea.codi.coop:codi.cooperatiu/codi-theme.git',
    'clone_url': 'http://gitea.codi.coop/codi.cooperatiu/codi-theme.git',
    'website': '',
    'stars_count': 0,
    'forks_count': 0,
    'watchers_count': 3,
    'open_issues_count': 0,
    'default_branch': 'master',
    'created_at': '2018-01-25T18:52:35Z',
    'updated_at': '2019-05-20T18:55:46Z',
    'permissions': {'admin': False,
                    'push': False,
                    'pull': True}}
    """


class GiteaRepository(Repository):
    __tablename__ = "gitea_repositories"

    gitea_id = db.Column(db.Integer)  # 2
    name = db.Column(db.String(200))  # "repo_name",
    owner_username = db.Column(db.String(200))  # "owner {username: username}",
    description = db.Column(db.Text)  # "repo description",
    empty = db.Column(db.Boolean)  # "False",
    private = db.Column(db.Boolean)  # "False",
    fork = db.Column(db.Boolean)  # "False",
    # parent = db.Column(db.Boolean)  # "None",
    mirror = db.Column(db.Boolean)  # "False",
    size = db.Column(db.Integer)  # "repo_name",
    html_url = db.Column(db.String(500), default="")
    website = db.Column(db.String(200))  # "repo_name",
    stars_count = db.Column(db.Integer)  # "repo_name",
    forks_count = db.Column(db.String(200))  # "repo_name",
    watchers_count = db.Column(db.Integer)  # "repo_name",
    open_issues_count = db.Column(db.Integer)  # "repo_name",
    default_branch = db.Column(db.String(200))  # "repo_name",
    created_at = db.Column(db.DateTime)  # "createdAt": "2014-03-09T05:10:10Z",
    updated_at = db.Column(db.DateTime)  # "updatedAt": "2014-03-09T16:57:19Z",
    pushed_at = db.Column(db.DateTime)  # "pushedAt": "2014-03-09T16:57:19Z",

    unified_select_statement_template = """
    select
        gitea_id as foreign_id,
        name as name,
        owner_username as username,
        description as description,
        created_at as created_at,
        updated_at as updated_at,
        pushed_at as pushed_at,
        stars_count as stars_count,
        forks_count as forks_count,
        private as is_private,
        fork as is_fork,
        false as is_archived,
        false as is_disabled,
        mirror as is_mirror,
        website as homepage_url,
        html_url as repo_url
    from
        {TABLE_NAME}
    where
        hosting_service_id = {HOSTING_SERVICE_ID}
    """

    @classmethod
    def from_dict(cls, hosting_service_id, d: dict, update=True):
        owner_username = d["owner"]["username"]
        name = d["name"]
        gitea_id = d["id"]

        repo = cls()

        repo.hosting_service_id = hosting_service_id
        repo.gitea_id = gitea_id
        repo.name = name
        repo.owner_username = owner_username
        repo.description = d["description"]
        repo.empty = d["empty"]
        repo.private = d["private"]
        repo.fork = d["fork"]
        repo.mirror = d["mirror"]
        repo.size = d["size"]
        repo.html_url = d["html_url"]
        repo.website = d["website"]
        repo.stars_count = d["stars_count"]
        repo.forks_count = d["forks_count"]
        repo.watchers_count = d["watchers_count"]
        repo.open_issues_count = d["open_issues_count"]
        repo.default_branch = d["default_branch"]
        repo.created_at = iso8601.parse_date(d["created_at"])
        repo.updated_at = iso8601.parse_date(d["updated_at"])

        return repo

    def to_dict(self) -> Dict[str, str]:
        repo = dict()
        repo["hosting_service_id"] = self.hosting_service_id
        repo["gitea_id"] = self.id
        repo["name"] = self.name
        repo["owner_username"] = self.owner_username
        repo["description"] = self.description
        repo["empty"] = self.empty
        repo["private"] = self.private
        repo["fork"] = self.fork
        repo["mirror"] = self.mirror
        repo["size"] = self.size
        repo["html_url"] = self.html_url
        repo["website"] = self.website
        repo["stars_count"] = self.stars_count
        repo["forks_count"] = self.forks_count
        repo["watchers_count"] = self.watchers_count
        repo["open_issues_count"] = self.open_issues_count
        repo["default_branch"] = self.default_branch
        repo["created_at"] = self.created_at
        repo["updated_at"] = self.updated_at
        return repo
