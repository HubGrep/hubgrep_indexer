import click
from flask import Blueprint, render_template
from flask import current_app as app, request
from flask import jsonify

from hubgrep_indexer.models.hosting_service import HostingService
from hubgrep_indexer import db

from hubgrep_indexer.api_blueprint import api

# todo: needs_auth
@api.route("/hosters", methods=["GET", "POST"])
def hosters():
    if request.method == "GET":
        hosting_services = []
        for hosting_service in HostingService.query.all():
            hosting_services.append(hosting_service.to_dict())
        return jsonify(hosting_service)
    elif request.method == "POST":
        """
        dict(
            type="github",
            landingpage_url="https://...",
            api_url="https://...",
            config="{...}"
        )
        """

        hosting_service = HostingService.from_dict(request.json())
        db.session.add(hosting_service)
        db.session.save()
        return jsonify(hosting_service)

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
