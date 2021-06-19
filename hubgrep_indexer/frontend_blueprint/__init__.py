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
            api_url=hosting_service.api_url,
            highest_id=state_manager.get_current_highest_repo_id(hosting_service.id),
        )
        services_highest_ids.append(d)

    return jsonify(services_highest_ids)
