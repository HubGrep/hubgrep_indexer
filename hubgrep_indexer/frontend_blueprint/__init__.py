from flask import Blueprint, render_template, jsonify
from flask import current_app as app

frontend = Blueprint("frontend", __name__)

from hubgrep_indexer import db, state_manager

from hubgrep_indexer.models.hosting_service import HostingService
from hubgrep_indexer.models.repositories.gitea import GiteaRepository


@frontend.route("/")
def index():
    services_highest_ids = []
    for hosting_service in HostingService.query.all():
        d = dict(
            hoster_name=hosting_service.hoster_name,
            repos=hosting_service.count(),
        )
        services_highest_ids.append(d)

    return jsonify(sorted(services_highest_ids, key=lambda d: d["repos"], reverse=True))


@frontend.route("/exports")
def exports():
    exports = []
    for hosting_service in HostingService.query.all():
        d = {hosting_service.hoster_name: hosting_service.to_dict()}
        exports.append(d)

    return jsonify(exports)
