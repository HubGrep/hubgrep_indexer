import logging
from typing import Union

from hubgrep_indexer.constants import HOST_TYPE_GITHUB, HOST_TYPE_GITEA, HOST_TYPE_GITLAB
from hubgrep_indexer.lib.state_manager.abstract_state_manager import AbstractStateManager, Block

logger = logging.getLogger(__name__)


class IStateHelper:
    # maximum of returned callbacks containing no results, before we blind-reset
    empty_results_max = 5

    @staticmethod
    def resolve_state(hosting_service_id: str,
                      state_manager: AbstractStateManager,
                      block_uid: str,
                      repo_dicts: list) -> Union[bool, None]:
        """
        Default implementation for resolving if we have consumed all
        repositories available, and its time to start over.

        This assumes that we give out blocks based on pagination,
        and reaching the end of pagination means we reset the
        state and start over.

        Returns state_manager.get_run_is_finished() OR None
        - true if we reached end, None if block is unrelated to the current run
        """
        block = state_manager.get_block(
            hoster_prefix=hosting_service_id, block_uid=block_uid)

        if not block:
            # Block has already been deleted from the previous run, no state changes
            logger.info(f"block no longer exists - no state changes, uid: {block_uid}")
            return None
        else:
            run_created_ts = state_manager.get_run_created_ts(
                hoster_prefix=hosting_service_id)
            is_block_from_old_run = block.run_created_ts != run_created_ts
            if is_block_from_old_run:
                logger.info(f"skipping state update for outdated block, uid: {block_uid}")
                # this Block belongs to an old run, so we avoid touching any state for it
                return None

        state_manager.finish_block(
            hoster_prefix=hosting_service_id, block_uid=block_uid)

        if len(repo_dicts) == 0:
            state_manager.increment_empty_results_counter(
                hoster_prefix=hosting_service_id, amount=1)
        else:
            state_manager.set_empty_results_counter(
                hoster_prefix=hosting_service_id, count=0)

        has_reached_end = IStateHelper.has_reached_end(
            hosting_service_id=hosting_service_id,
            state_manager=state_manager,
            repo_dicts=repo_dicts,
            block=block)
        has_too_many_empty = IStateHelper.has_too_many_consecutive_empty_results(
            hosting_service_id=hosting_service_id,
            state_manager=state_manager)

        if has_reached_end:
            logger.info(
                f'crawler reached end for hoster: {hosting_service_id}')
            state_manager.finish_run(hoster_prefix=hosting_service_id)
            return state_manager.get_run_is_finished(hosting_service_id)
        elif has_too_many_empty:
            logger.info(
                f'crawler reach max empty results for hoster: {hosting_service_id}')
            state_manager.finish_run(hoster_prefix=hosting_service_id)
            return state_manager.get_run_is_finished(hosting_service_id)
        else:
            # if we hit this branch, we are somewhere in the middle of the hoster.
            # we just count up our confirmed ids and go on
            if isinstance(block.ids, list) and len(block.ids) > 0:
                repo_id = block.ids[-1]
            else:
                repo_id = block.to_id
            state_manager.set_highest_confirmed_repo_id(
                hoster_prefix=hosting_service_id, repo_id=repo_id)
            return state_manager.get_run_is_finished(hosting_service_id)

    @staticmethod
    def has_too_many_consecutive_empty_results(
            hosting_service_id: str,
            state_manager: AbstractStateManager) -> bool:
        has_too_many_empty_results = state_manager.get_empty_results_counter(
            hoster_prefix=hosting_service_id) >= IStateHelper.empty_results_max
        return has_too_many_empty_results

    @staticmethod
    def has_reached_end(
            hosting_service_id: str,
            state_manager: AbstractStateManager,
            block: Block,
            repo_dicts: list) -> bool:
        """
        Try to find out if we reached the end of repos on this hoster.

        This should be the case, if we have an empty result set
        on the last handed-out block
        """

        # get the highest repo id we have seen
        highest_confirmed_id = state_manager.get_highest_confirmed_repo_id(
            hoster_prefix=hosting_service_id)

        # get end of the block behind the last confirmed one
        last_block_id = highest_confirmed_id + state_manager.batch_size

        # check if thats the block :)
        is_confirmed_next = block.to_id == last_block_id

        # we dont assume end on partially filled results, only on empty
        return is_confirmed_next and len(repo_dicts) == 0


class GitHubStateHelper(IStateHelper):
    empty_results_max = 100

    @staticmethod
    def has_reached_end(
            hosting_service_id: str,
            state_manager: AbstractStateManager,
            block: Block,
            repo_dicts: list) -> bool:
        """
        We default to False for GitHub as we receive lots of gaps within results.
        Maybe a whole block contains private
        repos and we get nothing back - therefore we cannot assume that we have
        reached the end when a block is empty.

        We instead rely on "IStateHelper.has_too_many_consecutive_empty_results(...)"
        to resolve and reset GitHub.
        """
        return False


class GiteaStateHelper(IStateHelper):
    pass


class GitLabStateHelper(IStateHelper):
    pass


def get_state_helper(hosting_service_type):
    state_helpers = {
        HOST_TYPE_GITHUB: GitHubStateHelper,
        HOST_TYPE_GITEA: GiteaStateHelper,
        HOST_TYPE_GITLAB: GitLabStateHelper
    }
    return state_helpers[hosting_service_type]
