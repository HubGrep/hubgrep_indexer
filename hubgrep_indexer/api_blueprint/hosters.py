from flask import request
from flask import jsonify

import logging

from hubgrep_indexer.models.hosting_service import HostingService
from hubgrep_indexer import db

from hubgrep_indexer.api_blueprint import api

logger = logging.getLogger(__name__)


# todo: needs_auth
@api.route("/hosters", methods=["GET", "POST"])
def hosters():
    if request.method == "GET":
        hosting_services = []
        for hosting_service in HostingService.query.all():
            hosting_services.append(hosting_service.to_dict(include_secrets=True))
        return jsonify(hosting_services)

    elif request.method == "POST":
        """
        dict(
            type="github",
            landingpage_url="https://...",
            api_url="https://...",
            config="{...}"
        )
        """

        hosting_service = HostingService.from_dict(request.json)
        db.session.add(hosting_service)
        db.session.commit()
        return jsonify(hosting_service.to_dict())


