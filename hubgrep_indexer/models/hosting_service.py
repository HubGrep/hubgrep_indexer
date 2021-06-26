import csv
import re
import json
from urllib.parse import urljoin
import logging

from flask import current_app
from typing import BinaryIO
from hubgrep_indexer.constants import (
    HOST_TYPE_GITHUB,
    HOST_TYPE_GITEA,
    HOST_TYPE_GITLAB,
)
from hubgrep_indexer.models.repositories.gitea import GiteaRepository
from hubgrep_indexer.models.repositories.github import GithubRepository
from hubgrep_indexer.models.repositories.gitlab import GitlabRepository


from hubgrep_indexer import db


logger = logging.getLogger(__name__)


class HostingService(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(80), nullable=False)

    # main instance website
    landingpage_url = db.Column(db.String(500))

    # should this be unique, or can we use it to store multiple
    # api keys for a backend?
    api_url = db.Column(db.String(500), unique=True, nullable=False)

    latest_export_json_gz = db.Column(db.String(500))

    api_key = db.Column(db.String(500), nullable=True)

    @property
    def hoster_name(self):
        from urllib.parse import urlparse

        return urlparse(self.landingpage_url).netloc

    def get_request_headers(self):
        """
        get request headers for this service

        todo:
            discuss: does this belong to the crawler?
        """
        if self.type == "github":
            return dict(access_token=self.api_key)
        elif self.type == "gitea":
            return {}
        elif self.type == "gitlab":
            return {"PRIVATE-TOKEN": self.api_key}
        else:
            logger.error(f"unknown hoster {self.type}!")
            return {}

    def get_service_label(self):
        return re.split("//", self.landingpage_url)[1].rstrip("/")

    def to_dict(self, include_secrets=False):
        results_base_url = current_app.config["RESULTS_BASE_URL"]
        latest_export_json_gz_url = None
        if self.latest_export_json_gz:
            latest_export_json_gz_url = urljoin(
                results_base_url, self.latest_export_json_gz
            )
        d = dict(
            id=self.id,
            type=self.type,
            landingpage_url=self.landingpage_url,
            api_url=self.api_url,
            hoster_name=self.hoster_name,
            latest_export_json_gz=latest_export_json_gz_url,
        )
        if include_secrets:
            d["api_key"] = self.api_key
        return d

    def crawler_dict(self):
        d = dict(
            id=self.id,
            type=self.type,
            api_url=self.api_url,
            request_headers=self.get_request_headers(),
        )
        return d

    @classmethod
    def from_dict(cls, d: dict):
        hosting_service = HostingService()
        hosting_service.type = d["type"]
        hosting_service.landingpage_url = d["landingpage_url"]
        hosting_service.api_url = d["api_url"]
        hosting_service.api_key = d.get("api_key", "")

        return hosting_service

    def get_csv(self, buffer: BinaryIO):
        fieldnames = ["type", "landingpage_url", "api_url"]
        dict_writer = csv.DictWriter(
            buffer,
            fieldnames=fieldnames,
            delimiter=";",
        )
        dict_writer.writeheader()
        dict_writer.writerow(self.to_dict())
        return buffer

    @property
    def repo_class(self):
        RepoClasses = {
            HOST_TYPE_GITHUB: GithubRepository,
            HOST_TYPE_GITEA: GiteaRepository,
            HOST_TYPE_GITLAB: GitlabRepository,
        }
        return RepoClasses[self.type]

    @property
    def repos(self):
        return self.repo_class.query.filter_by(hoster=self)
