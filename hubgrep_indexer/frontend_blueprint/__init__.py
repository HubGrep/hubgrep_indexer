from flask import Blueprint, render_template, jsonify
from flask import current_app as app

frontend = Blueprint("frontend", __name__)

from hubgrep_indexer import db, get_state_manager

from hubgrep_indexer.models.hosting_service import HostingService
from hubgrep_indexer.models.repositories.gitea import GiteaRepository


@frontend.route("/")
def index():
    services_highest_ids = []
    for hosting_service in HostingService.query.all():
        d = dict(
                hosting_service.to_dict()
        )
        services_highest_ids.append(d)

    return jsonify(services_highest_ids)


@frontend.route("/exports")
def exports():
    exports = []
    for hosting_service in HostingService.query.all():
        d = {hosting_service.hoster_name: hosting_service.to_dict()}
        exports.append(d)

    return jsonify(exports)
