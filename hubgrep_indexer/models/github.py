import json
import logging
from hubgrep_indexer import db

logger = logging.getLogger(__name__)


class GithubRepository(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    github_id = db.Column(db.Integer)  # "MDEwOlJlcG9zaXRvcnkxNzU1ODIyNg==",
    name = db.Colum(db.String(200))  # "service.subtitles.thelastfantasy",
    homepage_url = db.Column(db.String(200))  # "homepageUrl": null,
    url = db.Column(db.String(200)) # "url": "https://github.com/taxigps/service.subtitles.thelastfantasy",
    created_at = db.Column(db.DateTime)  # "createdAt": "2014-03-09T05:10:10Z",
    updated_at = db.Column(db.DateTime)  # "updatedAt": "2014-03-09T16:57:19Z",
    pushed_at = db.Column(db.DateTime)  # "pushedAt": "2014-03-09T16:57:19Z",
    short_description_html = db.Column(db.Text)  # "shortDescriptionHTML": "",
    description = db.Column(db.Text)  # "description": null,
    is_archived = db.Column(db.Bool)  # "isArchived": false,
    is_private = db.Column(db.Bool)  # "isPrivate": false,

    is_fork = db.Column(db.Bool)  # "isFork": false,
    is_empty = db.Column(db.Bool)  # "isEmpty": false,

    is_disabled = db.Column(db.Bool)  # "isDisabled": false,

    is_locked = db.Column(db.Bool)  # isLocked": false,
    is_template = db.Column(db.Bool)  # "isTemplate": false,
    stargazer_count = db.Column(db.Integer)  # "stargazerCount": 0,
    fork_coung = db.Column(db.Integer)  # "forkCount": 0,
    disk_usage = db.Column(db.Integer)  # "diskUsage": 192,
    owner_login = db.Column(db.String(200)) #  "owner": {"login": "taxigps","id": "MDQ6VXNlcjEwMjQzNA==","url": "https://github.com/taxigps"
    #"repositoryTopics": {
    #    "nodes": []
    #},
    primary_language_name = db.Column(db.String(200))  # "primaryLanguage": {"name": "Python"},
    license_name = db.Column(db.String(200))  #  "licenseInfo": {"name": "GNU General Public License v2.0", "nickname": "GNU GPLv2" }}
    license_nickname = db.Column(db.String(200))  #  "licenseInfo": {"name": "GNU General Public License v2.0", "nickname": "GNU GPLv2" }}


