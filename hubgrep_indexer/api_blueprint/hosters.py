import click
from flask import Blueprint, render_template
from flask import current_app as app, request
from flask import jsonify

from hubgrep_indexer.models.hosting_service import HostingService
from hubgrep_indexer import db, state_manager

from hubgrep_indexer.api_blueprint import api

# todo: needs_auth
@api.route("/hosters", methods=["GET", "POST"])
def hosters():
    if request.method == "GET":
        hosting_services = []
        for hosting_service in HostingService.query.all():
            hosting_services.append(hosting_service.to_dict())
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



@api.route("/hosters/<hosting_service_id>/state")
def state(hosting_service_id: int):
    return dict(
        current_round=dict(start_timestamp=1234567),
        blocks=[
            dict(from_id=1000, to_id=2000, timestamp=1234567, uid=54321),
            dict(from_id=2000, to_id=3000, timestamp=2345678, uid=65432),
            dict(
                from_id=0,
                to_id=1000,
                created_at=1234567,
                uid=76543,
                attempts_at=[
                    1234567,
                ],
                status="(constants like 'free' or 'crawling')",
            ),
        ],
    )

# /hosters/<id>  ?
@api.route("/hosters/<hosting_service_id>/block")
def get_block(hosting_service_id: int):
    timed_out_block = state_manager.get_timed_out_block(hosting_service_id)
    if timed_out_block:
        return jsonify(timed_out_block.to_dict())

    next_block = state_manager.get_next_block(hosting_service_id)
    return jsonify(next_block.to_dict())

    """
    return dict(
        timestamp=1234566,
        uid="some_uid",
        callback_url="www.post.done/type/github/<hoster_id>/",
        # if we already have ids
        ids=[1, 2, 3],
        # else for when we dont have known ids
        start=0,
        end=1000,
    )

    # or, noting todo:
    return {
        "status": "no_crawl",  # (not exactly so, but something explicit)
        "retry_at": 1234567,
    }
    """


@api.route("/hosters/<hosting_service_id>/", methods=["post"])
def add_repos(hosting_service_id: int):
    return None
