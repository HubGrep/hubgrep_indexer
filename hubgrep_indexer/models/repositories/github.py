import base64
from iso8601 import iso8601
import json
import logging
from hubgrep_indexer import db

logger = logging.getLogger(__name__)


class GithubRepository(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    hosting_service_id = db.Column(
        db.Integer, db.ForeignKey("hosting_service.id"), nullable=False
    )
    hosting_service = db.relationship("HostingService")

    github_id = db.Column(db.Integer)  # "MDEwOlJlcG9zaXRvcnkxNzU1ODIyNg==",
    name = db.Column(db.String(200))  # "service.subtitles.thelastfantasy",
    homepage_url = db.Column(db.String(200))  # "homepageUrl": null,
    url = db.Column(db.String(200))  # "url": "https://github.com/taxigps/service.subtitles.thelastfantasy",
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

        repo = cls.query.filter_by(
            hosting_service_id=hosting_service_id,
            owner_login=owner_login,
            name=name,
        ).first()
        if not update and not repo:
            raise Exception("repo not found!")
        if not repo:
            repo = cls()

        repo.hosting_service_id = hosting_service_id
        repo.github_id = repo.github_id_from_base64(d['id'])
        repo.name = name
        repo.homepage_url = d['homepageUrl']
        repo.url = d['url']
        repo.created_at = iso8601.parse_date(d['createdAt'])
        repo.updated_at = iso8601.parse_date(d['updatedAt'])
        repo.pushed_at = iso8601.parse_date(d['pushedAt'])
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
