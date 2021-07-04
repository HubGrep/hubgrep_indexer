"""
helpers to generate block dicts for the crawlers
"""

import logging
import time

from typing import Dict

from flask import url_for
from flask import current_app

from hubgrep_indexer import state_manager
from hubgrep_indexer.models.hosting_service import HostingService

logger = logging.getLogger(__name__)


def _state_is_too_old(state):
    ts_old_run = time.time() - current_app.config['OLD_RUN_AGE']
    created_ts_too_old = state["run_created_ts"] < ts_old_run
    if not state["run_is_finished"] or created_ts_too_old:
        return True
    return False


def _get_block_dict(hosting_service_id) -> Dict:
    timed_out_block = state_manager.get_timed_out_block(hosting_service_id)
    if timed_out_block:
        logger.info(f"re-attempting timed out block, uid: {timed_out_block.uid}")
        block = timed_out_block
    else:
        block = state_manager.get_next_block(hosting_service_id)
    block_dict = block.to_dict()

    hosting_service = HostingService.query.get(hosting_service_id)
    logger.info(f"getting block for {hosting_service}")

    block_dict["crawler"] = hosting_service.crawler_dict()
    block_dict["callback_url"] = url_for(
        "api.add_repos",
        hosting_service_id=hosting_service.id,
        block_uid=block_dict["uid"],
        _external=True,
    )
    return block_dict


def get_block_for_crawler(hoster_id) -> Dict:
    state = state_manager.get_state_dict(hoster_id)
    if _state_is_too_old(state):
        return _get_block_dict(hoster_id)
    return None


def get_loadbalanced_block_for_crawler(type) -> Dict:
    """
    get a block from a hoster of type <type>.

    behaviour is still a bit wonky.

    In the first round, running from an empty state_manager,
    this will hand out the first block of each hoster in order they come from
    the db, because the "run_created_ts" is initially `0`, and is then updated
    to `time.time()` on the first created block.

    That means that everything with created_ts==0 will be run for the first block,
    and then it will complete a whole hoster, then the next one...
    """
    # get all states
    hoster_id_state = {}
    for hosting_service in HostingService.query.filter_by(type=type).all():
        hoster_id_state[hosting_service.id] = state_manager.get_state_dict(
            hosting_service.id
        )

    # remove everything finished recently
    crawlable_hosters = {}
    for hoster_id, state in hoster_id_state.items():
        logger.debug(f"checking hoster {hoster_id}")
        if _state_is_too_old(state):
            logger.debug(f"hoster {hoster_id} would be crawlable...")
            crawlable_hosters[hoster_id] = state

    if not crawlable_hosters:
        # everything up to date, nothing to do
        logger.warning("no crawlable hosters!")
        return None

    # get the oldest one in crawlable_hosters
    oldest_hoster_id, oldest_hoster_state = min(
        crawlable_hosters.items(),
        key=lambda d: d[1].get(
            "run_created_ts",
        ),
    )
    logger.debug(f"creating block for hoster {oldest_hoster_id}:")
    logger.debug(f"state {oldest_hoster_state}:")
    return _get_block_dict(oldest_hoster_id)
