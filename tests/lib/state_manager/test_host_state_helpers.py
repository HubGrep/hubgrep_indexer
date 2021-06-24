import pytest

from hubgrep_indexer.constants import HOST_TYPE_GITHUB, HOST_TYPE_GITLAB, HOST_TYPE_GITEA
from hubgrep_indexer.lib.state_manager.abstract_state_manager import LocalStateManager, AbstractStateManager
from hubgrep_indexer.lib.state_manager.host_state_helpers import get_state_helper

HOSTER_PREFIX = "hoster_1"
HOSTER_TYPES = [HOST_TYPE_GITHUB, HOST_TYPE_GITLAB, HOST_TYPE_GITEA]


class TestHostStateHelpers:
    @pytest.fixture()
    def state_manager(self):
        manager = LocalStateManager()
        yield manager
        manager.reset(HOSTER_PREFIX)

    @pytest.mark.parametrize('hoster_type', HOSTER_TYPES)
    def test_state_helpers_has_reached_end(self, hoster_type: str, state_manager: AbstractStateManager):
        print(f'testing for: {hoster_type}')
        # init state for a already completed block
        old_block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
        state_manager.set_highest_confirmed_repo_id(hoster_prefix=HOSTER_PREFIX, repo_id=old_block.to_id)
        state_manager.finish_block(hoster_prefix=HOSTER_PREFIX, block_uid=old_block.uid)

        repos = []  # we're testing against what happens when we receive empty results
        new_block = state_manager.get_next_block(HOSTER_PREFIX)
        state_helper = get_state_helper(hoster_type)
        has_reached_end = state_helper.has_reached_end(hosting_service_id=HOSTER_PREFIX,
                                                       state_manager=state_manager,
                                                       block=new_block,
                                                       repo_dicts=repos)
        if hoster_type == HOST_TYPE_GITHUB:
            # github should not assume end on single empty results
            assert has_reached_end is False
        else:
            assert has_reached_end is True

    @pytest.mark.parametrize('hoster_type', HOSTER_TYPES)
    def test_state_helpers_too_many_consecutive_empty(self, hoster_type, state_manager: AbstractStateManager):
        print(f'testing for: {hoster_type}')
        state_helper = get_state_helper(hoster_type)
        state_manager.set_empty_results_counter(hoster_prefix=HOSTER_PREFIX, count=state_helper.empty_results_max)
        has_too_many = state_helper.has_too_many_consecutive_empty_results(hosting_service_id=HOSTER_PREFIX,
                                                                           state_manager=state_manager)
        assert has_too_many is True

    @pytest.mark.parametrize('hoster_type', HOSTER_TYPES)
    def test_state_helpers_resolve_state_continue(self, hoster_type, state_manager: AbstractStateManager):
        print(f'testing for: {hoster_type}')
        old_block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
        state_helper = get_state_helper(hoster_type)
        repos = [{"id": id} for id in range(state_manager.batch_size)]  # repos found by crawling the "old_block"
        state_helper.resolve_state(hosting_service_id=HOSTER_PREFIX,
                                   state_manager=state_manager,
                                   block_uid=old_block.uid,
                                   repo_dicts=repos)

        new_block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)  # consider this awaiting results still
        new_run_created_ts = state_manager.get_run_created_ts(hoster_prefix=HOSTER_PREFIX)
        new_highest_confirmed_id = state_manager.get_highest_confirmed_repo_id(hoster_prefix=HOSTER_PREFIX)
        new_highest_block_id = state_manager.get_highest_block_repo_id(hoster_prefix=HOSTER_PREFIX)
        blocks = state_manager.get_blocks(hoster_prefix=HOSTER_PREFIX)
        assert len(blocks) == 1
        assert new_block.uid in blocks
        assert old_block.uid not in blocks
        assert new_run_created_ts == old_block.run_created_ts
        assert new_run_created_ts == new_block.run_created_ts
        assert new_highest_confirmed_id == state_manager.batch_size
        assert new_highest_block_id == state_manager.batch_size * 2

    @pytest.mark.parametrize('hoster_type', HOSTER_TYPES)
    def test_state_helpers_resolve_state_reset(self, hoster_type, state_manager: AbstractStateManager):
        print(f'testing for: {hoster_type}')
        # init with an old block state (attempt to raise side-effects to fail this test, if we introduce them)
        old_block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
        state_manager.set_highest_confirmed_repo_id(hoster_prefix=HOSTER_PREFIX, repo_id=old_block.to_id)
        state_manager.finish_block(hoster_prefix=HOSTER_PREFIX, block_uid=old_block.uid)
        new_block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)

        state_helper = get_state_helper(hoster_type)
        if (hoster_type == HOST_TYPE_GITHUB):
            # making sure that github resolves into state-reset as well
            state_manager.set_empty_results_counter(hoster_prefix=HOSTER_PREFIX,
                                                    count=state_helper.empty_results_max - 1)

        repos = []  # with no results, all but github should trigger a state-reset
        state_helper.resolve_state(hosting_service_id=HOSTER_PREFIX,
                                   state_manager=state_manager,
                                   block_uid=new_block.uid,
                                   repo_dicts=repos)

        blocks = state_manager.get_blocks(hoster_prefix=HOSTER_PREFIX)
        new_run_created_ts = state_manager.get_run_created_ts(hoster_prefix=HOSTER_PREFIX)
        assert len(blocks) == 0
        assert new_run_created_ts != old_block.run_created_ts
