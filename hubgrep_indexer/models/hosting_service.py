import time
import re
from urllib.parse import urljoin
from urllib.parse import urlparse
import logging

import datetime
from typing import List, Dict

from sqlalchemy.engine import ResultProxy
from sqlalchemy import func

from flask import current_app

from hubgrep_indexer import db
from hubgrep_indexer.models.repositories.abstract_repository import Repository
from hubgrep_indexer.models.export import Export

logger = logging.getLogger(__name__)


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

    def get_exports_dict(self, unified=False) -> List[Dict]:
        """
        shorthand for the query to this hosters exports, sorted by datetime
        (newest first)
        """
        query = Export.query.filter_by(hosting_service_id=self.id, is_raw=(not unified))
        query.order_by(Export.created_at.desc())

        results_base_url = current_app.config["RESULTS_BASE_URL"]
        exports = []
        for export in query:
            export_url = urljoin(results_base_url, export.file_path)
            exports.append(
                dict(
                    created_at=export.created_at.isoformat(),
                    url=export_url,
                    repo_count=export.repo_count,
                )
            )
        return exports

    def _get_default_export_filename(self, timestamp: datetime, unified=False):
        date_str = timestamp.strftime("%Y%m%d_%H%M")
        export_base_name = f"{self.hoster_name}"
        export_base_name += "_unified" if unified else "_raw"
        filename_suffix = f"_{date_str}.csv.gz"
        export_filename = export_base_name + filename_suffix
        return export_filename

    def export_repositories(self, unified=False, export_filename=None):
        """
        Export this hosters repositories to a gzipped json file.

        returns `Export` (needs to be commited to the db!)
        """
        repo_count = self.count()

        now = datetime.datetime.now()
        if not export_filename:
            export_filename = self._get_default_export_filename(now, unified)

        repo_class: Repository = Repository.repo_class_for_type(self.type)
        before = time.time()
        if not unified:
            repo_class.export_csv_gz(self.id, self.type, export_filename)
        else:
            repo_class.export_unified_csv_gz(self.id, self.type, export_filename)
        logger.info(f"exporting {repo_count} repos took {time.time() - before}s")

        export = Export()
        export.created_at = now
        export.file_path = export_filename
        export.hosting_service_id = self.id
        export.repo_count = repo_count
        export.is_raw = not unified
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

        d = dict(
            id=self.id,
            type=self.type,
            landingpage_url=self.landingpage_url,
            api_url=self.api_url,
            hoster_name=self.hoster_name,
            exports_raw=self.get_exports_dict(unified=False),
            exports_unified=self.get_exports_dict(unified=True),
        )
        if include_secrets:
            d["api_key"] = self.api_key
            d["request_headers"] = self.get_request_headers()
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
