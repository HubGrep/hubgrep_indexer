from hubgrep_indexer.api_blueprint import api
from flask import request

from hubgrep_indexer.models.github import GitHubUser
from hubgrep_indexer.models.platforms import Platform
from hubgrep_indexer import db, state_manager


@api.route("/types/github/<hosting_service_id>/state")
def github_state(hosting_service_id: int):
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


@api.route("/types/github/<hosting_service_id/block>")
def get_github_block(hosting_service_id: int):
    timed_out_block = state_manager.get_timed_out_block()
    if timed_out_block:
        return timed_out_block.to_json()
    next_block = state_manager.get_next_block()
    return next_block.to_json()

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


@api.route("/types/github/<hosting_service_id>/", methods=["post"])
def github_add_repos(hosting_service_id: int):
    return None
