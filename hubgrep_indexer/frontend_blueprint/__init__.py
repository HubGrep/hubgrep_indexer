from flask import Blueprint
from flask import jsonify

from hubgrep_indexer.models.hosting_service import HostingService

frontend = Blueprint("frontend", __name__)


@frontend.route("/")
def index():
    services_highest_ids = []
    for hosting_service in HostingService.query.all():
        services_highest_ids.append(hosting_service.to_dict())

    return jsonify(sorted(services_highest_ids, key=lambda d: d["num_repos"], reverse=True))

