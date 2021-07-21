import logging
import time
import re
import datetime
from typing import List, Dict
from urllib.parse import urljoin
from urllib.parse import urlparse
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.engine import ResultProxy
from sqlalchemy import func
from flask import current_app

from hubgrep_indexer import db
from hubgrep_indexer.models.repositories.abstract_repository import Repository
from hubgrep_indexer.models.export_meta import ExportMeta

logger = logging.getLogger(__name__)


class HostingService(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(80), nullable=False)

    # main instance website
    landingpage_url = db.Column(db.String(500))

    api_url = db.Column(db.String(500), unique=True, nullable=False)
    api_keys = db.Column(ARRAY(db.String(500)), nullable=True)

    def __str__(self) -> str:
        return f"<HostingService {self.type}-{self.id}@{self.hoster_name}>"

    @property
    def hoster_name(self):
        return str(urlparse(self.landingpage_url).netloc)

    def get_exports_dict(self, unified=False) -> List[Dict]:
        """
        Shorthand for the query to this hosters exports, sorted by datetime (newest first).
        """
        query = ExportMeta.query.filter_by(hosting_service_id=self.id, is_raw=(not unified))
        query.order_by(ExportMeta.created_at.desc())

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

    def _get_default_export_filename(self, timestamp: datetime, unified=False) -> str:
        """
        Generate an export file-name.

        returns something like "codeberg.org_unified_20211231_1200.csv.gz"
        """
        date_str = timestamp.strftime("%Y%m%d_%H%M")
        export_base_name = f"{self.hoster_name}"
        export_base_name += "_unified" if unified else "_raw"
        filename_suffix = f"_{date_str}.csv.gz"
        export_filename = export_base_name + filename_suffix
        return export_filename

    def export_repositories(self, unified=False, export_filename=None) -> ExportMeta:
        """
        Export this hosters repositories to a gzipped json file.

        returns `ExportMeta` (needs to be commited to the db!)
        """
        now = datetime.datetime.now()
        if not export_filename:
            export_filename = self._get_default_export_filename(now, unified)

        logger.debug(f"exporting repos for {self}...")
        repo_class: Repository = Repository.repo_class_for_type(self.type)
        before = time.time()
        if not unified:
            repo_class.export_csv_gz(self.id, self.type, export_filename)
        else:
            repo_class.export_unified_csv_gz(self.id, self.type, export_filename)
        repo_count = self.count_repos()
        logger.info(f"exporting {repo_count} repos took {time.time() - before}s")

        export = ExportMeta()
        export.created_at = now
        export.file_path = export_filename
        export.hosting_service_id = self.id
        export.repo_count = repo_count
        export.is_raw = not unified
        return export

    def get_crawler_request_headers(self):
        """
        Get crawler request headers for this service.

        These are in addition to authorization, which is handled with api_key in the crawler itself.
        """
        headers = dict()
        # TODO append hoster specific headers when required/found
        if self.type == "github":
            pass
        elif self.type == "gitea":
            pass
        elif self.type == "gitlab":
            pass
        else:
            logger.error(f"unknown HostingService.type: {self.type}!")
        return headers

    def get_service_label(self):
        return re.split("//", self.landingpage_url)[1].rstrip("/")

    def to_dict(self, include_secrets: bool = False, api_key: str = None):
        """
        Dict representation for this HostingService.

        If "include_secrets" is True, api_keys and any additional crawler headers are included.
        If "include_secrets" is True and "api_key" is provided, it will replace "api_keys" property with "api_key".
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
            if api_key:
                d["api_key"] = api_key
            else:
                d["api_keys"] = self.api_keys
            d["crawler_request_headers"] = self.get_crawler_request_headers()
        return d

    @classmethod
    def from_dict(cls, d: dict):
        hosting_service = HostingService()
        hosting_service.type = d["type"]
        hosting_service.landingpage_url = d["landingpage_url"]
        hosting_service.api_url = d["api_url"]
        hosting_service.api_keys = d.get("api_keys", [])

        return hosting_service

    @property
    def repos(self) -> ResultProxy:
        """
        Get all repositories for this hoster.

        call like hoster.repos.all() (or whatever you want to do with it)
        """
        repo_class = Repository.repo_class_for_type(self.type)
        return repo_class.query.filter_by(hosting_service=self)

    def count_repos(self) -> int:
        repo_class = Repository.repo_class_for_type(self.type)
        # fast counting: https://gist.github.com/hest/8798884
        return db.session.execute(
            db.session.query(repo_class)
            .filter_by(hosting_service_id=self.id, is_completed=True)
            .statement.with_only_columns([func.count()])
            .order_by(None)
        ).scalar()
