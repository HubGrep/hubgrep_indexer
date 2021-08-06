import json
import click
import logging

from hubgrep_indexer.models.hosting_service import HostingService
from hubgrep_indexer.cli_blueprint import cli_bp
from hubgrep_indexer import db, state_manager

logger = logging.getLogger(__name__)


@cli_bp.cli.command(help="export hosting_service objects as json (printed out)")
def export_hosters():
    services = []
    for hosting_service in HostingService.query.all():
        services.append(hosting_service.to_dict(include_secrets=True))
    print(json.dumps(services, indent=2))


@cli_bp.cli.command(help="import hosting_service objects from a json file")
@click.argument("json_path", type=click.Path())
def import_hosters(json_path):
    with open(json_path, "r") as f:
        hoster_dicts = json.loads(f.read())

        for hoster in hoster_dicts:
            # TODO be backwards compatible, for now - delete this condition after updating our prod hosters
            if "api_key" in hoster and "api_keys" not in hoster:
                hoster["api_keys"] = [hoster["api_key"]]

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


@cli_bp.cli.command(help="unlock an api_key from being attached to a machine_id")
@click.argument("hosting_service_id")
@click.argument("api_key")
def unlock_api_key(hosting_service_id, api_key):
    state_manager.remove_machine_api_key(hosting_service_id=hosting_service_id, api_key=api_key)


@cli_bp.cli.command(help="print all currently active api_keys (attached to a machine_id)")
def active_api_keys():
    lines = []
    for hosting_service in HostingService.query.all():
        if isinstance(hosting_service.api_keys, list):
            for api_key in hosting_service.api_keys:
                if state_manager.is_api_key_active(hosting_service_id=hosting_service.id, api_key=api_key):
                    machine_id = state_manager.get_machine_id_by_api_key(hosting_service_id=hosting_service.id,
                                                                         api_key=api_key)
                    lines.append(
                        f"machine_id: {machine_id} locks api_key: {api_key} for hosting_service_id: {hosting_service.id}")
    if len(lines) > 0:
        print("\n".join(lines))
    else:
        print("- no currently active api_keys -")
