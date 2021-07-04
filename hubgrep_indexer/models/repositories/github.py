import base64
from iso8601 import iso8601
import json
import logging
from typing import Dict

from hubgrep_indexer import db

from hubgrep_indexer.models.repositories.abstract_repository import Repository

from sqlalchemy import Index
logger = logging.getLogger(__name__)


class GithubRepository(Repository):
    __tablename__ = "github_repositories"
    __table_args__ = (Index('repo_ident_index_github', "id", "github_id"), )

    github_id = db.Column(db.Integer)  # "MDEwOlJlcG9zaXRvcnkxNzU1ODIyNg==",
    name = db.Column(db.String(200))  # "service.subtitles.thelastfantasy",
    homepage_url = db.Column(db.String(500))  # "homepageUrl": null,
    url = db.Column(db.String(500))  # "url": "https://github.com/taxigps/service.subtitles.thelastfantasy",
    created_at = db.Column(db.DateTime)  # "createdAt": "2014-03-09T05:10:10Z",
    updated_at = db.Column(db.DateTime)  # "updatedAt": "2014-03-09T16:57:19Z",
    pushed_at = db.Column(db.DateTime)  # "pushedAt": "2014-03-09T16:57:19Z",
    short_description_html = db.Column(db.Text)  # "shortDescriptionHTML": "",
    description = db.Column(db.Text)  # "description": null,
    is_archived = db.Column(db.Boolean)  # "isArchived": false,
    is_private = db.Column(db.Boolean)  # "isPrivate": false,

    is_fork = db.Column(db.Boolean)  # "isFork": false,
    is_empty = db.Column(db.Boolean)  # "isEmpty": false,

    is_disabled = db.Column(db.Boolean)  # "isDisabled": false,

    is_locked = db.Column(db.Boolean)  # isLocked": false,
    is_template = db.Column(db.Boolean)  # "isTemplate": false,
    stargazer_count = db.Column(db.Integer)  # "stargazerCount": 0,
    fork_count = db.Column(db.Integer)  # "forkCount": 0,
    disk_usage = db.Column(db.Integer)  # "diskUsage": 192,
    owner_login = db.Column(
        db.String(200))  # "owner": {"login": "taxigps","id": "MDQ6VXNlcjEwMjQzNA==","url": "https://github.com/taxigps"
    # "repositoryTopics": {
    #    "nodes": []
    # },
    primary_language_name = db.Column(db.String(200))  # "primaryLanguage": {"name": "Python"},
    license_name = db.Column(
        db.String(200))  # "licenseInfo": {"name": "GNU General Public License v2.0", "nickname": "GNU GPLv2" }}
    license_nickname = db.Column(
        db.String(200))  # "licenseInfo": {"name": "GNU General Public License v2.0", "nickname": "GNU GPLv2" }}

    @classmethod
    def github_id_from_base64(cls, gql_id: str) -> int:
        """
        transform githubs graphql ids to their actual ids
        """
        # "MDEwOlJlcG9zaXRvcnkxNzU1ODIyNg==" => b'010:Repository17558226'
        decoded = base64.b64decode(gql_id).decode()
        repo_id = int(decoded.split("Repository")[1])
        return repo_id

    @classmethod
    def from_dict(cls, hosting_service_id, d: dict, update=True) -> "GithubRepository":
        owner_login = d['owner']['login']
        name = d['name']
        github_id = cls.github_id_from_base64(d['id'])

        repo = cls.query.filter_by(
            hosting_service_id=hosting_service_id,
            github_id=github_id
        ).first()
        if not update and not repo:
            raise Exception("repo not found!")
        if not repo:
            repo = cls()

        repo.hosting_service_id = hosting_service_id
        repo.github_id = github_id
        repo.name = name
        repo.homepage_url = d['homepageUrl']
        repo.url = d['url']
        repo.created_at = iso8601.parse_date(d['createdAt'])
        repo.updated_at = iso8601.parse_date(d['updatedAt'])
        if d.get('pushedAt', None):
            repo.pushed_at = iso8601.parse_date(d['pushedAt'])
        else:
            repo.pushed_at = None
        repo.short_description_html = d['shortDescriptionHTML']
        repo.description = d['description']
        repo.is_archived = d['isArchived']
        repo.is_private = d['isPrivate']
        repo.is_fork = d['isFork']
        repo.is_empty = d['isEmpty']
        repo.is_disabled = d['isDisabled']
        repo.is_locked = d['isLocked']
        repo.is_template = d['isTemplate']
        repo.stargazer_count = d['stargazerCount']
        repo.fork_count = d['forkCount']
        repo.disk_usage = d['diskUsage']
        repo.owner_login = owner_login
        if isinstance(d['primaryLanguage'], dict):
            repo.primary_language_name = d['primaryLanguage'].get('name', None)
        if isinstance(d['licenseInfo'], dict):
            repo.license_name = d['licenseInfo'].get('name', None)
            repo.license_nickname = d['licenseInfo'].get('nickname', None)

        return repo

    def to_dict(self) -> Dict[str, str]:
        repo = dict()
        repo["hosting_service_id"] = self.hosting_service_id
        repo["github_id"] = self.github_id
        repo["name"] = self.name
        repo["homepage_url"] = self.homepage_url
        repo["url"] = self.url
        repo["created_at"] = self.created_at
        repo["updated_at"] = self.updated_at
        repo["pushed_at"] = self.pushed_at
        repo["short_description_html"] = self.short_description_html
        repo["description"] = self.description
        repo["is_archived"] = self.is_archived
        repo["is_private"] = self.is_private
        repo["is_fork"] = self.is_fork
        repo["is_empty"] = self.is_empty
        repo["is_disabled"] = self.is_disabled
        repo["is_locked"] = self.is_locked
        repo["is_template"] = self.is_template
        repo["stargazer_count"] = self.stargazer_count
        repo["fork_count"] = self.fork_count
        repo["disk_usage"] = self.disk_usage
        repo["owner_login"] = self.owner_login
        repo["primary_language_name"] = self.primary_language_name
        repo["license_name"] = self.license_name
        repo["license_nickname"] = self.license_nickname

