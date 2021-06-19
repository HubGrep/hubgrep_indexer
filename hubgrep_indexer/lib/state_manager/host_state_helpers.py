from hubgrep_indexer.constants import HOST_TYPE_GITHUB, HOST_TYPE_GITEA, HOST_TYPE_GITLAB
from hubgrep_indexer.lib.state_manager.abstract_state_manager import StateManager, Block


class IStateHelper:
    empty_results_max = 20  # maximum of returned callbacks containing no results, before we blind-reset

    @staticmethod
    def resolve_state(hosting_service_id: str, state_manager: StateManager, block_uid: str, repos_dict: dict):
        """
        Default implementation for resolving if we have consumed all repositories available, and its time to start over.

        This assumes that we give out blocks based on pagination, and reaching the end of pagination means we reset the
        state and start over.

        Importantly - this implementation is not intended for service_hosts that hand out empty results in the middle.
        """
        block = state_manager.get_blocks(hoster_prefix=hosting_service_id)[block_uid]
        state_manager.finish_block(hoster_prefix=hosting_service_id, block_uid=block_uid)

        if len(repos_dict) == 0:
            state_manager.increment_empty_results_counter(hoster_prefix=hosting_service_id, amount=1)

        has_reached_end = IStateHelper.has_reached_end(hosting_service_id=hosting_service_id,
                                                       state_manager=state_manager,
                                                       repos_dict=repos_dict,
                                                       block=block)
        has_too_many_empty = IStateHelper.has_too_many_consecutive_empty_results(hosting_service_id=hosting_service_id,
                                                                                 state_manager=state_manager)

        if has_reached_end or has_too_many_empty:
            state_manager.reset(hoster_prefix=hosting_service_id)
        elif not has_reached_end:
            state_manager.set_highest_confirmed_repo_id(hoster_prefix=hosting_service_id, repo_id=block.to_id)

    @staticmethod
    def has_too_many_consecutive_empty_results(hosting_service_id: str, state_manager: StateManager) -> bool:
        return \
            state_manager.get_empty_results_counter(hoster_prefix=hosting_service_id) > IStateHelper.empty_results_max

    @staticmethod
    def has_reached_end(hosting_service_id: str, state_manager: StateManager, block: Block, repos_dict: dict) -> bool:
        highest_confirmed_id = state_manager.get_highest_confirmed_repo_id(hoster_prefix=hosting_service_id)
        is_confirmed_next = block.to_id == highest_confirmed_id + state_manager.batch_size
        if is_confirmed_next and len(repos_dict) == 0:
            return True
        else:
            # TODO moved line outside because its a side-effect, but maybe its more obscure when moved out of here?
            # state_manager.set_highest_confirmed_repo_id(hoster_prefix=hosting_service_id, repo_id=block.to_id)
            return False


class GitHubStateHelper(IStateHelper):
    @staticmethod
    def has_reached_end(block_uid: str, repos_dict: dict, block: Block, state_manager: StateManager) -> bool:
        return False  # our github crawler will give us lots of gaps, let empty_counter decide instead.


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
