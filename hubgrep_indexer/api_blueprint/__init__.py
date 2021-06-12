import click
from flask import Blueprint, render_template
from flask import current_app as app, request
from flask import jsonify

api = Blueprint("api", __name__, url_prefix="/api/v1")


from hubgrep_indexer.api_blueprint.hosters import hosters
from hubgrep_indexer.api_blueprint.github import get_github_block

@api.route("/types")
def types():
    return jsonify(["github"])
