import json
import click
import logging

from hubgrep_indexer.models.hosting_service import HostingService
from hubgrep_indexer.cli_blueprint import cli_bp
from hubgrep_indexer import db, state_manager

logger = logging.getLogger(__name__)


def _release_api_key(hosting_service: HostingService, api_key: str):
    machine_id = state_manager.remove_machine_api_key(
        hosting_service_id=hosting_service.id, api_key=api_key
    )
    return machine_id


@cli_bp.cli.command(help="export hosting_service objects as json (printed out)")
@click.option("--include-exports", "-e", is_flag=True)
def export_hosters(include_exports: bool = False):
    services = []
    for hosting_service in HostingService.query.all():
        services.append(
            hosting_service.to_dict(
                include_secrets=True, include_exports=include_exports
            )
        )
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


@cli_bp.cli.command(help="release an api_key from being attached to a machine_id")
@click.argument("api_key")
def release_api_key(api_key):
    lines = []
    for hosting_service in HostingService.query.all():
        if api_key in hosting_service.api_keys:
            machine_id = _release_api_key(hosting_service, api_key)
            if machine_id is not None:
                # since we search, if for whatever reason there are duplicate api_keys, multiple will be released
                # it would then be good to know that this happened
                lines.append(
                    f"- released api_key from machine_id: {machine_id} for {hosting_service}"
                )
    if len(lines) > 0:
        print("\n".join(lines))
    else:
        print("- no active api-key to release was found! -")


@cli_bp.cli.command(
    help="print all currently active api_keys (attached to a machine_id)"
)
def active_api_keys():
    lines = []
    for hosting_service in HostingService.query.all():
        for api_key in hosting_service.api_keys:
            if state_manager.is_api_key_active(
                hosting_service_id=hosting_service.id, api_key=api_key
            ):
                machine_id = state_manager.get_machine_id_by_api_key(
                    hosting_service_id=hosting_service.id, api_key=api_key
                )
                lines.append(
                    f"- machine_id: {machine_id} holds api_key: {api_key} for {hosting_service}"
                )
    if len(lines) > 0:
        print("\n- ".join(lines))
    else:
        print("- no currently active api_keys! -")


@cli_bp.cli.command()
def list_api_keys():
    for hosting_service in HostingService.query.all():
        print(hosting_service.api_url)
        for api_key in hosting_service.api_keys:
            machine_id = state_manager.get_machine_id_by_api_key(
                hosting_service_id=hosting_service.id, api_key=api_key
            )
            print(f"\t{api_key} - used by {machine_id}")


@cli_bp.cli.command(help="add api key")
def add_api_key(api_url, api_key):
    hosting_service = HostingService.query.filter_by(api_url=api_url).first()
    if not hosting_service:
        print(f"couldnt find api url {api_url}!")
        exit()

    if api_key in hosting_service.api_keys:
        print("hoster already has this api key!")
        exit()

    hosting_service.add_api_key(api_key)
    db.session.add(hosting_service)
    db.session.commit()
    print("key added!")


@cli_bp.cli.command(help="delete an api key")
def delete_api_key(api_url, api_key):
    hosting_service = HostingService.query.filter_by(api_url=api_url).first()
    if not hosting_service:
        print(f"couldnt find api url {api_url}!")
        exit()

    if api_key not in hosting_service.api_keys:
        print("hoster doesnt have this api key!")
        exit()

    machine_id = state_manager.get_machine_id_by_api_key(
        hosting_service_id=hosting_service.id, api_key=api_key
    )
    if machine_id is not None:
        if not click.confirm("api key is in use. really delete?"):
            print("not doing it then...")
            exit(1)

        print("released api key")
        _release_api_key(hosting_service, api_key)

    hosting_service.delete_api_key(api_key)
    db.session.add(hosting_service)
    db.session.commit()
    print("deleted api key")
