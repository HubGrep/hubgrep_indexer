import time
import datetime
from flask import request
from flask import jsonify

import logging

from hubgrep_indexer.models.hosting_service import HostingService
from hubgrep_indexer.models.repositories.abstract_repository import Repository
from hubgrep_indexer.lib.block_helpers import (
    get_block_for_crawler,
    get_loadbalanced_block_for_crawler,
)
from hubgrep_indexer.lib.state_manager.abstract_state_manager import Block
from hubgrep_indexer.lib.state_manager.host_state_helpers import get_state_helper
from hubgrep_indexer import db, state_manager

from hubgrep_indexer.api_blueprint import api

logger = logging.getLogger(__name__)


# todo: needs_auth
@api.route("/hosters", methods=["GET", "POST"])
def hosters():
    if request.method == "GET":
        hosting_services = []
        for hosting_service in HostingService.query.all():
            hosting_services.append(hosting_service.crawler_dict())
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
        return jsonify(hosting_service.crawler_dict())


@api.route("/hosters/<hosting_service_id>/state", methods=['GET'])
def state(hosting_service_id: int):
    blocks = state_manager.get_blocks(hosting_service_id)
    block_dicts = [block.to_dict() for block in blocks.values()]
    return jsonify(block_dicts)
    """
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
    """


@api.route("/hosters/<type>/loadbalanced_block")
def get_loadbalanced_block(type: str):
    block_dict = get_loadbalanced_block_for_crawler(type)

    if not block_dict:
        return jsonify(Block.get_sleep_dict())
    else:
        return jsonify(block_dict)


@api.route("/hosters/<hosting_service_id>/block")
@api.route("/hosters/<hosting_service_id>/block", methods=['GET'])
def get_block(hosting_service_id: int):
    block_dict = get_block_for_crawler(hosting_service_id)

    if not block_dict:
        return jsonify(Block.get_sleep_dict())
    else:
        return jsonify(block_dict)

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

    # or, nothing to do:
    return {
        "status": "sleep",
        "retry_at": 1234567,
    }
    """


@api.route("/hosters/<hosting_service_id>/", methods=["PUT"])
@api.route("/hosters/<hosting_service_id>/<block_uid>", methods=["PUT"])
def add_repos(hosting_service_id: int, block_uid: int = None):
    """
    Add repository data used in our search-index.

    :param hosting_service_id: int - the registered hosting_service these repos belong to.
    :param block_uid: (optional) int - if this arg is missing the repos will be added without affecting internal state.
    """
    hosting_service: HostingService = HostingService.query.get(hosting_service_id)
    repo_dicts = request.json

    if not hosting_service.repo_class:
        return jsonify(status="error", msg="unknown repo type"), 500

    # add repos to the db :)
    for repo_dict in repo_dicts:
        repo_class = Repository.repo_class_for_type(self.type)
        r = repo_class.from_dict(hosting_service_id, repo_dict)
        db.session.add(r)
    db.session.commit()

    state_helper = get_state_helper(hosting_service.type)
    run_is_finished = state_helper.resolve_state(
        hosting_service_id=hosting_service_id,
        state_manager=state_manager,
        block_uid=block_uid,
        repo_dicts=repo_dicts,
    )
    if run_is_finished:
        now = datetime.datetime.now()
        date_str = now.strftime("%Y%m%d_%H%M")
        export_filename = f"{hosting_service.hoster_name}_{date_str}.json.gz"
        hosting_service.repo_class.export_json_gz(hosting_service_id, export_filename)
        hosting_service.latest_export_json_gz = export_filename
        db.session.add(hosting_service)
        db.session.commit()

    return jsonify(dict(status="ok")), 200
