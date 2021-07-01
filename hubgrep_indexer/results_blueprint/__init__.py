import click
from flask import Blueprint, render_template
from flask import current_app as app, request
from flask import jsonify
from flask import send_from_directory

results_bp = Blueprint("results", __name__, url_prefix="/results")


from hubgrep_indexer.api_blueprint.hosters import hosters


@results_bp.route('/<path:path>')
def send_js(path):
    return send_from_directory('../results/', path)
