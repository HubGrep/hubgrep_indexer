import time
import logging
from flask import jsonify
from flask_login import login_required

from hubgrep_indexer.lib.state_manager.abstract_state_manager import Block
from hubgrep_indexer.api_blueprint import api
from hubgrep_indexer.lib.block_helpers import (
    get_block_for_crawler,
    get_loadbalanced_block_for_crawler,
)
from hubgrep_indexer.models.hosting_service import HostingService

logger = logging.getLogger(__name__)


@api.route("/hosters/<type>/loadbalanced_block")
@login_required
def get_loadbalanced_block(type: str):
    ts_before = time.time()
    block_dict = get_loadbalanced_block_for_crawler(hosting_service_type=type)
    logger.debug(f"got a load-balanced block - took {time.time() - ts_before}s")

    if not block_dict:
        return jsonify(Block.get_sleep_dict())
    else:
        return jsonify(block_dict)


@api.route("/hosters/<hosting_service_id>/block")
@api.route("/hosters/<hosting_service_id>/block", methods=['GET'])
@login_required
def get_block(hosting_service_id: int):
    ts_before = time.time()
    hosting_service = HostingService.query.get(hosting_service_id)
    block_dict = get_block_for_crawler(hosting_service_id=hosting_service.id)
    logger.debug(f"got a block for {hosting_service} - took {time.time() - ts_before}s")

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
