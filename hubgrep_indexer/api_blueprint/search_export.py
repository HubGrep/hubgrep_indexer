from flask import jsonify

import logging

from hubgrep_indexer.models.hosting_service import HostingService

from hubgrep_indexer.api_blueprint import api

logger = logging.getLogger(__name__)


@api.route("/export_hosters", methods=["GET"])
def export_hosters():
    hosting_services = []
    for hosting_service in HostingService.query.all():
        hosting_services.append(hosting_service.to_dict())
    return jsonify(hosting_services)
