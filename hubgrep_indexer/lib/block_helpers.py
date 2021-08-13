"""
helpers to generate block dicts for the crawlers
"""

import logging
import time
from typing import Dict, Union
from flask import request
from flask import current_app

from hubgrep_indexer import state_manager
from hubgrep_indexer.constants import BLOCK_STATUS_READY, CRAWLER_HEADER_MACHINE_ID, CRAWLER_HEADER_CORRELATION_ID, \
    CRAWLER_MACHINE_ID_DEFAULT, CRAWLER_CORRELATION_ID_DEFAULT
from hubgrep_indexer.lib.utils import obscurify_secret
from hubgrep_indexer.models.hosting_service import HostingService

logger = logging.getLogger(__name__)


def _state_is_too_old(state):
    ts_old_run = time.time() - current_app.config["OLD_RUN_AGE"]
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
        has_run_hit_end = state_manager.get_has_run_hit_end(hoster_prefix=hosting_service_id)
        blocks_list = state_manager.get_blocks_list(hoster_prefix=hosting_service_id)
        if has_run_hit_end and blocks_list:
            # we hit the end, but blocks are still open - dont start the next run yet
            logger.debug("we have been asked for a block, but we hit the end and are still waiting for blocks")
            return None
        block = state_manager.get_next_block(hosting_service_id)

    hosting_service = HostingService.query.get(hosting_service_id)
    logger.info(f"getting block for {hosting_service}")

    api_key = resolve_api_key(hosting_service=hosting_service)
    block.hosting_service = hosting_service.to_dict(include_secrets=True, api_key=api_key)

    if block.status != BLOCK_STATUS_READY:
        logger.warning(f'expected block status "{BLOCK_STATUS_READY}" - block "{block}"')

    return block.to_dict()


def get_block_for_crawler(hosting_service_id) -> Union[Dict, None]:
    state = state_manager.get_state_dict(hoster_prefix=hosting_service_id)
    if _state_is_too_old(state):
        return _get_block_dict(hosting_service_id)
    return None


def get_loadbalanced_block_for_crawler(hosting_service_type: str) -> Union[Dict, None]:
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
    for hosting_service in HostingService.query.filter_by(type=hosting_service_type).all():
        hoster_id_state[hosting_service.id] = state_manager.get_state_dict(
            hoster_prefix=hosting_service.id
        )

    # remove everything finished recently
    crawlable_hosters = {}
    for hoster_id, state in hoster_id_state.items():
        # logger.debug(f"checking hoster {hoster_id}")
        if _state_is_too_old(state):
            # logger.debug(f"hoster {hoster_id} would be crawlable...")
            crawlable_hosters[hoster_id] = state

    if not crawlable_hosters:
        # everything up to date, nothing to do
        logger.warning("no crawlable hosters!")
        return None

    logger.debug(f"crawlable hosters: {crawlable_hosters.keys()}")
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


def resolve_api_key(hosting_service: HostingService) -> Union[str, None]:
    """
    Find an available api_key (one not already in use by another machine_id) and lock it from being
    distributed to other machine_ids. To unlock a api_key use our command "flask cli release_api_key".

    Machine-id is controlled via request header: "Hubgrep-Crawler-Machine-ID".

    We want to avoid any automatic/accidental sharing of api_keys between multiple
    crawler machines in order to avoid being flagged as abusive via ip addresses.
    """
    crawler_id = request.headers.get(CRAWLER_HEADER_CORRELATION_ID, CRAWLER_CORRELATION_ID_DEFAULT)
    machine_id = request.headers.get(CRAWLER_HEADER_MACHINE_ID, CRAWLER_MACHINE_ID_DEFAULT)

    api_key = state_manager.get_machine_api_key(hosting_service_id=hosting_service.id, machine_id=machine_id) or None
    if not api_key:
        for _api_key in hosting_service.api_keys:
            if not state_manager.is_api_key_active(hosting_service_id=hosting_service.id, api_key=_api_key):
                state_manager.set_machine_api_key(hosting_service_id=hosting_service.id,
                                                  machine_id=machine_id,
                                                  api_key=_api_key)
                api_key = _api_key
                logger.info(
                    f"crawler_id: {crawler_id} - assigned {hosting_service} api_key: {obscurify_secret(api_key)} to machine_id: {machine_id}")
                break
            # Potentially, all keys are active - we don't allow machines to share keys, so we resolve to None.
            # This also means we have to manually deactivate keys if we want to change machine-ids in crawlers.
            # This is because we want to avoid any automatic/accidental emitting of shared api_keys between
            # our different crawler "clusters", to avoid being flagged as abusive via ip addresses.

    key_to_log = obscurify_secret(api_key) if api_key else None
    logger.debug(
        f"crawler_id: {crawler_id} - resolved {hosting_service} api_key: {key_to_log} for machine_id: {machine_id}")
    return api_key
