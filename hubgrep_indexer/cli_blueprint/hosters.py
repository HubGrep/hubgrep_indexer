import json
import click
import logging

from hubgrep_indexer.models.hosting_service import HostingService

from hubgrep_indexer.cli_blueprint import cli_bp
from hubgrep_indexer import db

logger = logging.getLogger(__name__)


@cli_bp.cli.command()
def export_hosters():
    services = []
    for hosting_service in HostingService.query.all():
        services.append(hosting_service.to_dict(include_secrets=True))
    print(json.dumps(services, indent=2))


@cli_bp.cli.command()
@click.argument("json_path", type=click.Path())
def import_hosters(json_path):
    with open(json_path, "r") as f:
        hoster_dicts = json.loads(f.read())

        for hoster in hoster_dicts:
            try:
                hosting_service = HostingService.from_dict(hoster)
                if not HostingService.query.filter_by(
                    api_url=hosting_service.api_url
                ).first():
                    logger.info(f"adding {hosting_service.api_url}")
                    db.session.add(hosting_service)
                    db.session.commit()
                else:
                    logger.info(f"skipping {hosting_service.api_url} (already added)")
            except Exception as e:
                logger.exception(e)
