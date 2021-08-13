import logging
from typing import Union, List

from hubgrep_indexer.lib.block import Block
from hubgrep_indexer.constants import (
    HOST_TYPE_GITHUB,
    HOST_TYPE_GITEA,
    HOST_TYPE_GITLAB,
)
from hubgrep_indexer.models.hosting_service import HostingService
from hubgrep_indexer import state_manager

logger = logging.getLogger(__name__)


class IStateHelper:
    # maximum consecutive returned callbacks containing no results, before we blind-reset
    # only relevant for non-paginated results when overriding IStateHelper.has_reached_end (github)
    empty_results_max = 100

    @classmethod
    def resolve_state(
            cls,
            hosting_service: HostingService,
            block_uid: str,
            parsed_repos: list,
    ) -> Union[bool, None]:
        """
        Default implementation for resolving if we have consumed all
        repositories available, and its time to start over.

        This assumes that we give out blocks based on pagination,
        and reaching the end of pagination means we reset the
        state and start over.

        Returns state_manager.get_run_is_finished() OR None
        - true/false if we reached end, None if block is unrelated to the current run
        """
        logger.info(f"resolving state for {block_uid}")
        run_created_ts = state_manager.get_run_created_ts(hoster_prefix=hosting_service.id)
        block = state_manager.get_block(hoster_prefix=hosting_service.id, block_uid=block_uid)

        # 1 - first part of "run state" is to guard against touching state for old/invalid blocks
        if not block:
            # Block has already been deleted from the previous run, no state changes
            logger.warning(f"{hosting_service} - block no longer exists - no run state changes, uid: {block_uid}")
            return None
        if block.run_created_ts != run_created_ts:
            logger.warning(f"{hosting_service} - skipping run state update but finishing outdated block: {block}")
            state_manager.finish_block(hoster_prefix=hosting_service.id, block_uid=block.uid)
            return None

        # 2 - now we start making updates depending on what the results (repos/block) tells us
        state_manager.finish_block(
            hoster_prefix=hosting_service.id, block_uid=block_uid
        )
        if len(parsed_repos) == 0:
            state_manager.increment_empty_results_counter(hoster_prefix=hosting_service.id, amount=1)
        else:
            state_manager.set_empty_results_counter(hoster_prefix=hosting_service.id, count=0)

        # check on the effects of the block transaction
        has_reached_end = cls.has_reached_end(
            hosting_service=hosting_service,
            parsed_repos=parsed_repos,
            block=block,
        )
        has_too_many_empty_results = cls.has_too_many_consecutive_empty_results(
            hosting_service=hosting_service,
        )

        if has_reached_end:
            logger.info(f"{hosting_service} - run has reached end")
            state_manager.set_has_run_hit_end(hoster_prefix=hosting_service.id, has_hit_end=True)
        elif has_too_many_empty_results:
            logger.info(f"{hosting_service} - run has reached max empty results")
            state_manager.set_has_run_hit_end(hoster_prefix=hosting_service.id, has_hit_end=True)
        else:
            # we are somewhere in the middle of a hosters repos
            # and we count up our confirmed ids and continue
            if isinstance(block.ids, list) and len(block.ids) > 0:
                repo_id = block.ids[-1]
            else:
                repo_id = block.to_id
            state_manager.set_highest_confirmed_block_repo_id(hoster_prefix=hosting_service.id, repo_id=repo_id)

        # 3 - indicate if a run is over, or still needs work
        has_run_hit_end = state_manager.get_has_run_hit_end(hoster_prefix=hosting_service.id)
        if has_run_hit_end:
            # the run is finished (as in, we hit the end), but we may have blocks open
            # we dont want to trigger export-and-rotate until the blocks at least time out/max retries
            dead_blocks = state_manager.delete_dead_blocks(hoster_prefix=hosting_service.id)
            if dead_blocks:
                logger.warning(f"{hosting_service} - deleted dead blocks: {dead_blocks}")

            active_blocks = cls.get_active_blocks(hosting_service=hosting_service, run_created_ts=run_created_ts)
            if len(active_blocks) > 0:
                logger.info(
                    f"{hosting_service} - run will finish once all remaining open blocks are finished: {active_blocks}")
                return False

            logger.info(f"{hosting_service} - run completed - last processed block: {block}")
            return True
        else:
            return False


    @classmethod
    def get_active_blocks(cls, hosting_service: HostingService, run_created_ts: float) -> List[Block]:
        """ Retrieve all blocks still active in the current run. """
        active_blocks = []
        for block in state_manager.get_blocks_list(hoster_prefix=hosting_service.id):
            if block.run_created_ts == run_created_ts and not block.is_dead():
                active_blocks.append(block)
        return active_blocks

    @classmethod
    def has_too_many_consecutive_empty_results(cls, hosting_service: HostingService) -> bool:
        has_too_many_empty_results = (
                state_manager.get_empty_results_counter(hoster_prefix=hosting_service.id)
                >= cls.empty_results_max
        )
        return has_too_many_empty_results

    @classmethod
    def has_reached_end(cls, hosting_service: HostingService, block: Block, parsed_repos: list) -> bool:
        """
        Try to find out if we reached the end of repos on this hoster.

        This should only be the case, if we have an empty result set
        on the last handed-out block.

        This method assumes that results are coming from a paginated source,
        such that reaching 0 results means there are no more pages. We also
        give a little bit of extra leeway by allowing partial results before
        we reach our conclusion that it's the end of pagination.
        """
        # we dont reason about partially filled results, only check/assume end of run if we reached 0 results
        if len(parsed_repos) > 0:
            return False

        # get the ending repo id from a block we have seen containing results
        highest_confirmed_id = state_manager.get_highest_confirmed_block_repo_id(
            hoster_prefix=hosting_service.id
        )

        # get ending repo id of the block after the last confirmed one
        last_block_id = highest_confirmed_id + state_manager.batch_size
        # check if our current empty block comes after a block with confirmed results
        return block.to_id == last_block_id


class GitHubStateHelper(IStateHelper):
    @classmethod
    def has_reached_end(cls, hosting_service: HostingService, block: Block, parsed_repos: list) -> bool:
        """
        We default to False for GitHub as we receive lots of gaps within results.
        Maybe a whole block contains private repos and we get nothing back,
        therefore we cannot assume that we have reached the end when a block is empty.

        We instead rely on "IStateHelper.has_too_many_consecutive_empty_results(...)"
        to resolve and reset GitHub.
        """
        return False


class GiteaStateHelper(IStateHelper):
    pass


class GitLabStateHelper(IStateHelper):
    pass


def get_state_helper(hosting_service: HostingService):
    state_helpers = {
        HOST_TYPE_GITHUB: GitHubStateHelper,
        HOST_TYPE_GITEA: GiteaStateHelper,
        HOST_TYPE_GITLAB: GitLabStateHelper,
    }
    return state_helpers[hosting_service.type]()
