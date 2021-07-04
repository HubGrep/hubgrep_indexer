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
@click.argument("json_path", type=click.Path())
def export_repos(hosting_service, json_path):
    hosting_service = HostingService.query.filter_by(api_url=hosting_service).first()
    export = hosting_service.export_repositories()
    db.session.add(export)
    db.session.commit()


@cli_bp.cli.command()
@click.option("--keep", type=int, default=3)
@click.option(
    "--hosting-service",
    type=str,
    help="api_url of the hosting service (eg. https://api.github.com/)",
)
def cleanup_exports(keep=None, hosting_service=None):
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
            os.remove(file_abspath)
            db.session.delete(export)
        db.session.commit()
