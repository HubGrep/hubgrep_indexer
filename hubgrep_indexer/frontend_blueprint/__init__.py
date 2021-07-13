from flask import Blueprint
from flask import jsonify

from hubgrep_indexer.models.hosting_service import HostingService
from hubgrep_indexer import state_manager

frontend = Blueprint("frontend", __name__)


@frontend.route("/")
def index():
    services_highest_ids = []
    for hosting_service in HostingService.query.all():
        services_highest_ids.append(hosting_service.to_dict())

    return jsonify(sorted(services_highest_ids, key=lambda d: d["id"], reverse=True))


@frontend.route("/state")
def state():
    states = {}
    for hosting_service in HostingService.query.all():
        states[hosting_service.hoster_name] = dict(
            state=state_manager.get_state_dict(hosting_service.id),
            id=hosting_service.id,
        )
    return jsonify(states)
