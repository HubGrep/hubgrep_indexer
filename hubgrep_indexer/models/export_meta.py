import os
import datetime
import time
import logging
from typing import TYPE_CHECKING
from pathlib import Path

from flask import current_app

from hubgrep_indexer import db
from hubgrep_indexer.models.repositories.abstract_repository import Repository

if TYPE_CHECKING:
    from hubgrep_indexer.models.hosting_service import HostingService

logger = logging.getLogger(__name__)


class ExportMeta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hosting_service = db.relationship("HostingService")
    hosting_service_id = db.Column(
        db.Integer, db.ForeignKey("hosting_service.id"), nullable=False
    )

    is_raw = db.Column(db.Boolean, nullable=True)

    created_at = db.Column(db.DateTime(), nullable=False)
    file_path = db.Column(
        db.String(500), nullable=True
    )  # None is indicating that the file has likely been removed

    repo_count = db.Column(db.Integer, nullable=True)

    def __str__(self):
        return f"Export {self.hosting_service.hoster_name} @ {self.created_at}"

    def delete_file(self):
        file_abspath = Path(current_app.config["RESULTS_PATH"]).joinpath(self.file_path)
        try:
            os.remove(file_abspath)
        except FileNotFoundError:
            logger.warning(f"(ignoring) could'nt find and delete {file_abspath}")

        self.file_path = None
        db.session.commit()

    @classmethod
    def _get_default_export_filename(
        cls,
        hosting_service: "HostingService",
        timestamp: datetime.datetime,
        unified=False,
    ):
        """
        returns something like "codeberg.org_unified_20211231_1200.csv.gz"
        """
        date_str = timestamp.strftime("%Y%m%d_%H%M")
        export_base_name = f"{hosting_service.hoster_name}"
        export_base_name += "_unified" if unified else "_raw"
        filename_suffix = f"_{date_str}.csv.gz"
        export_filename = export_base_name + filename_suffix
        return export_filename

    @classmethod
    def create_export(
        cls,
        hosting_service: "HostingService",
        table_name,
        unified=False,
        export_filename=None,
    ) -> str:
        """
        Export this hosters repositories to a gzipped json file.

        returns `Export` (needs to be commited to the db!)
        """
        now = datetime.datetime.now()
        if not export_filename:
            export_filename = cls._get_default_export_filename(
                hosting_service, now, unified
            )

        logger.debug(f"exporting repos for {hosting_service}...")
        repo_class: Repository = Repository.repo_class_for_type(hosting_service.type)
        before = time.time()
        if not unified:
            repo_class.export_csv_gz(table_name, hosting_service, export_filename)
        else:
            repo_class.export_unified_csv_gz(
                table_name, hosting_service, export_filename
            )
        repo_count = hosting_service.count_repos()
        logger.info(f"exporting {repo_count} repos took {time.time() - before}s")

        export = cls()
        export.created_at = now
        export.file_path = export_filename
        export.hosting_service_id = hosting_service.id
        export.repo_count = repo_count
        export.is_raw = not unified
        return export
