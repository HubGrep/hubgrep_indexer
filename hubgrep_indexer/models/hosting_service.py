import re
from urllib.parse import urljoin
from urllib.parse import urlparse
import logging

import datetime

from sqlalchemy.engine import ResultProxy
from sqlalchemy import func

from flask import current_app

from hubgrep_indexer import db
from hubgrep_indexer.models.repositories.abstract_repository import Repository

logger = logging.getLogger(__name__)


class Export(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hosting_service = db.relationship("HostingService")
    hosting_service_id = db.Column(
        db.Integer, db.ForeignKey("hosting_service.id"), nullable=False
    )

    created_at = db.Column(db.DateTime(), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)

    def __str__(self):
        return f"Export {self.hosting_service.hoster_name} @ {self.created_at}"


class HostingService(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(80), nullable=False)

    # main instance website
    landingpage_url = db.Column(db.String(500))

    # should this be unique, or can we use it to store multiple
    # api keys for a backend?
    api_url = db.Column(db.String(500), unique=True, nullable=False)
    api_key = db.Column(db.String(500), nullable=True)

    @property
    def hoster_name(self):
        return str(urlparse(self.landingpage_url).netloc)

    def get_exports(self):
        """
        shorthand for the query to this hosters exports, sorted by datetime
        (newest first)
        """
        return (
            Export.query.filter_by(hosting_service_id=self.id)
            .order_by(Export.created_at.desc())
        )

    def export_repositories(self, export_filename=None):
        """
        Export this hosters repositories to a gzipped json file.

        returns `Export` (needs to be commited to the db!)
        """
        if not export_filename:
            now = datetime.datetime.now()
            date_str = now.strftime("%Y%m%d_%H%M")
            export_filename = f"{self.hoster_name}_{date_str}.json.gz"

        repo_class = Repository.repo_class_for_type(self.type)
        repo_class.export_json_gz(self.id, export_filename)

        export = Export()
        export.created_at = now
        export.file_path = export_filename
        export.hosting_service_id = self.id
        return export

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
        """
        return the dict for this hoster.

        includes the result url, and things we might want to have in an api later.
        """
        exports = []
        results_base_url = current_app.config["RESULTS_BASE_URL"]
        for export in self.get_exports():
            export_url = urljoin(
                results_base_url, export.file_path
            )
            exports.append(dict(created_at=export.created_at, url=export_url))

        d = dict(
            id=self.id,
            type=self.type,
            landingpage_url=self.landingpage_url,
            api_url=self.api_url,
            hoster_name=self.hoster_name,
            exports=exports,
            num_repos=self.count(),
        )
        if include_secrets:
            d["api_key"] = self.api_key
        return d

    def crawler_dict(self):
        """
        return the dict which is sent to a crawler as part of the block
        """
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

    @property
    def repos(self) -> ResultProxy:
        """
        get all repositories for this hoster.

        call like hoster.repos.all() (or whatever you want to do with it)
        """
        repo_class = Repository.repo_class_for_type(self.type)
        return repo_class.query.filter_by(hosting_service=self)

    def count(self) -> int:
        repo_class = Repository.repo_class_for_type(self.type)
        # fast counting: https://gist.github.com/hest/8798884
        return db.session.execute(
            db.session.query(repo_class)
            .filter_by(hosting_service_id=self.id)
            .statement.with_only_columns([func.count()])
            .order_by(None)
        ).scalar()
