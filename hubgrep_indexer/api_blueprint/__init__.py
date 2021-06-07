import click
from flask import Blueprint, render_template
from flask import current_app as app, request
from flask import jsonify

api = Blueprint("api", __name__, url_prefix="/api/v1")

from hubgrep_indexer.models.platforms import HostingService


# todo: needs_auth
@api.route("/hosters")
def hosters():
    [
        {
            # is this our PK?
            "api_url": "https://...",
            # config for this hoster in hubgrep_search
            # api key isnt needed for local search, and shouldnt be handed out
            "landingpage_url": "https://...",
            "label": "some_label",
            "type": "gitea",
            # gzipped csv export
            "export_url": "https://path/to/export_some_label_2021-01-01.csv.gz",
            "export_date": "2021-01-01...",
        },
    ]


@api.route("/types")
def types():
    return jsonify(["github"])
