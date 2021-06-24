from hubgrep_indexer.constants import HOST_TYPE_GITHUB, HOST_TYPE_GITEA, HOST_TYPE_GITLAB
from hubgrep_indexer.lib.state_manager.abstract_state_manager import AbstractStateManager, Block


class IStateHelper:
    empty_results_max = 5  # maximum of returned callbacks containing no results, before we blind-reset

    @staticmethod
    def resolve_state(hosting_service_id: str, state_manager: AbstractStateManager, block_uid: str, repo_dicts: list):
        """
        Default implementation for resolving if we have consumed all repositories available, and its time to start over.

        This assumes that we give out blocks based on pagination, and reaching the end of pagination means we reset the
        state and start over.
        """
        block = state_manager.get_blocks(hoster_prefix=hosting_service_id)[block_uid]
        if block.run_created_ts != state_manager.get_run_created_ts(hoster_prefix=hosting_service_id):
            return  # this block belongs to an old run, so we avoid touching any state for it
        state_manager.finish_block(hoster_prefix=hosting_service_id, block_uid=block_uid)

        if len(repo_dicts) == 0:
            state_manager.increment_empty_results_counter(hoster_prefix=hosting_service_id, amount=1)

        has_reached_end = IStateHelper.has_reached_end(hosting_service_id=hosting_service_id,
                                                       state_manager=state_manager,
                                                       repo_dicts=repo_dicts,
                                                       block=block)
        has_too_many_empty = IStateHelper.has_too_many_consecutive_empty_results(hosting_service_id=hosting_service_id,
                                                                                 state_manager=state_manager)

        if has_reached_end:
            state_manager.reset(hoster_prefix=hosting_service_id)
        elif has_too_many_empty:
            state_manager.reset(hoster_prefix=hosting_service_id)
        else:
            if isinstance(block.ids, list) and len(block.ids) > 0:
                repo_id = block.ids[-1]
            else:
                repo_id = block.to_id
            state_manager.set_highest_confirmed_repo_id(hoster_prefix=hosting_service_id, repo_id=repo_id)

    @staticmethod
    def has_too_many_consecutive_empty_results(hosting_service_id: str, state_manager: AbstractStateManager) -> bool:
        return \
            state_manager.get_empty_results_counter(hoster_prefix=hosting_service_id) >= IStateHelper.empty_results_max

    @staticmethod
    def has_reached_end(hosting_service_id: str, state_manager: AbstractStateManager, block: Block, repo_dicts: list) -> bool:
        highest_confirmed_id = state_manager.get_highest_confirmed_repo_id(hoster_prefix=hosting_service_id)
        is_confirmed_next = block.to_id == highest_confirmed_id + state_manager.batch_size
        # we dont assume end on partially filled results, only on empty
        return is_confirmed_next and len(repo_dicts) == 0


class GitHubStateHelper(IStateHelper):
    empty_results_max = 20

    @staticmethod
    def has_reached_end(hosting_service_id: str, state_manager: AbstractStateManager, block: Block, repo_dicts: list) -> bool:
        """
        We default to False for GitHub as we receive lots of gaps within results. Maybe a whole block contains private
        repos and we get nothing back - therefore we cannot assume that we have reached the end when a block is empty.

        We instead rely on "IStateHelper.has_too_many_consecutive_empty_results(...)" to resolve and reset GitHub.
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
