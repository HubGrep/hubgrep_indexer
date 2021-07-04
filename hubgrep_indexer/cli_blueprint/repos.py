import os
import click
from flask import current_app
from pathlib import Path
import logging

from hubgrep_indexer.models.hosting_service import HostingService, Export

from hubgrep_indexer.cli_blueprint import cli_bp
from hubgrep_indexer import db

logger = logging.getLogger(__name__)


@cli_bp.cli.command()
@click.argument("hosting_service")
def export_repos(hosting_service):
    hosting_service = HostingService.query.filter_by(api_url=hosting_service).first()
    export = hosting_service.export_repositories()
    print(f"exported to {export.file_path}")
    db.session.add(export)
    db.session.commit()


@cli_bp.cli.command()
@click.option("--keep", type=int, default=3)
@click.option(
    "--hosting-service",
    type=str,
    help="api_url of the hosting service (eg. https://api.github.com/)",
)
def cleanup_exports(keep, hosting_service=None):
    if hosting_service:
        q = HostingService.query.filter_by(api_url=hosting_service)
    else:
        q = HostingService.query
    for hosting_service in q.all():
        old_exports = (
            Export.query.filter_by(hosting_service_id=hosting_service.id)
            .order_by(Export.created_at.desc())
            .offset(keep)
        )

        for export in old_exports:
            print(f"deleting export {export}")
            file_abspath = Path(current_app.config["RESULTS_PATH"]).joinpath(
                export.file_path
            )
            try:
                os.remove(file_abspath)
            except FileNotFoundError:
                print(f"couldnt find {file_abspath} - deleting the db entry")
            db.session.delete(export)
        db.session.commit()
