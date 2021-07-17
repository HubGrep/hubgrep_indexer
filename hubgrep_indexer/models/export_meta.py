import os
import logging
from pathlib import Path

from flask import current_app

from hubgrep_indexer import db

logger = logging.getLogger(__name__)


class ExportMeta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hosting_service = db.relationship("HostingService")
    hosting_service_id = db.Column(
        db.Integer, db.ForeignKey("hosting_service.id"), nullable=False
    )

    is_raw = db.Column(db.Boolean, nullable=True)

    created_at = db.Column(db.DateTime(), nullable=False)
    file_path = db.Column(db.String(500), nullable=True)  # indicating that the file has likely been removed

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
