import time
from flask import request
from flask import jsonify

import logging
from typing import List

from hubgrep_indexer.models.hosting_service import HostingService
from hubgrep_indexer.models.repositories.github import GithubRepository
from hubgrep_indexer.models.repositories.gitea import GiteaRepository
from hubgrep_indexer.constants import (
    HOST_TYPE_GITHUB,
    HOST_TYPE_GITEA,
    HOST_TYPE_GITLAB,
)
from hubgrep_indexer.lib.block_helpers import (
    get_block_for_crawler,
    get_loadbalanced_block_for_crawler,
)

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


@api.route("/hosters/<hosting_service_id>/state")
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
        sleep_dict = {
            "status": "sleep",
            "retry_at": time.time() + 300,  # 5min from now
        }
        return jsonify(sleep_dict)

    return jsonify(block_dict)


@api.route("/hosters/<hosting_service_id>/block")
def get_block(hosting_service_id: int):
    block_dict = get_block_for_crawler(hosting_service_id)
    if not block_dict:
        sleep_dict = {
            "status": "sleep",
            "retry_at": time.time() + 300,  # 5min from now
        }
        return jsonify(sleep_dict)
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

    # or, noting todo:
    return {
        "status": "no_crawl",  # (not exactly so, but something explicit)
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

    # get repo class
    RepoClasses = {
        HOST_TYPE_GITHUB: GithubRepository,
        HOST_TYPE_GITEA: GiteaRepository
        # HOST_TYPE_GITLAB: not implemented
    }
    RepoClass = RepoClasses.get(hosting_service.type)
    if not RepoClass:
        return jsonify(status="error", msg="unknown repo type"), 500

    # add repos to the db :)
    for repo_dict in repo_dicts:
        r = RepoClass.from_dict(hosting_service_id, repo_dict)
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
        # todo: make export
        pass

    return jsonify(dict(status="ok")), 200
