import redislite
import pytest

from hubgrep_indexer.lib.state_manager.abstract_state_manager import LocalStateManager, AbstractStateManager
from hubgrep_indexer.lib.state_manager.redis_state_manager import RedisStateManager


HOSTER_PREFIX = "hoster_1"


class TestLocalStateManager:
    @pytest.fixture()
    def state_manager(self):
        manager = LocalStateManager()
        yield manager
        manager.reset(HOSTER_PREFIX)

    def test_set_get_highest_repo_id(self, state_manager: AbstractStateManager):
        assert state_manager.get_highest_block_repo_id(hoster_prefix=HOSTER_PREFIX) == 0
        state_manager.set_highest_block_repo_id(hoster_prefix=HOSTER_PREFIX, repo_id=1)
        assert state_manager.get_highest_block_repo_id(hoster_prefix=HOSTER_PREFIX) == 1
        state_manager.set_highest_block_repo_id(hoster_prefix=HOSTER_PREFIX, repo_id=0)
        assert state_manager.get_highest_block_repo_id(hoster_prefix=HOSTER_PREFIX) == 0

    def test_get_next_block(self, state_manager: AbstractStateManager):
        # to_id should be batch_size for the first block
        block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
        assert block.from_id == 1
        assert block.to_id == state_manager.batch_size

        # second block should start at end of first block+1
        block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
        assert block.from_id == state_manager.batch_size + 1

    def test_get_timed_out_block(self, state_manager: AbstractStateManager):
        block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
        block_timeout = block.attempts_at[0] + state_manager.block_timeout + 1
        timed_out_block = state_manager.get_timed_out_block(
            hoster_prefix=HOSTER_PREFIX, timestamp_now=block_timeout
        )

        assert block.uid == timed_out_block.uid

    def test_delete_block(self, state_manager: AbstractStateManager):
        block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
        assert len(state_manager.get_blocks(hoster_prefix=HOSTER_PREFIX).keys()) == 1
        state_manager._delete_block(hoster_prefix=HOSTER_PREFIX, block_uid=block.uid)
        assert len(state_manager.get_blocks(hoster_prefix=HOSTER_PREFIX).keys()) == 0

    def test_finish_block(self, state_manager: AbstractStateManager):
        self.test_delete_block(state_manager=state_manager)

    def test_run_created_ts(self, state_manager: AbstractStateManager):
        initial_run_created_ts = state_manager.get_run_created_ts(hoster_prefix=HOSTER_PREFIX)
        state_manager.reset(hoster_prefix=HOSTER_PREFIX)
        second_run_created_ts = state_manager.get_run_created_ts(hoster_prefix=HOSTER_PREFIX)
        assert initial_run_created_ts
        assert second_run_created_ts
        assert initial_run_created_ts != second_run_created_ts

    def test_empty_results_counter(self, state_manager: AbstractStateManager):
        new_count = 1
        initial_counter_state = state_manager.get_empty_results_counter(hoster_prefix=HOSTER_PREFIX)
        state_manager.set_empty_results_counter(hoster_prefix=HOSTER_PREFIX, count=new_count)
        second_counter_state = state_manager.get_empty_results_counter(hoster_prefix=HOSTER_PREFIX)
        assert initial_counter_state == 0
        assert second_counter_state == new_count

    def test_reset(self, state_manager: AbstractStateManager):
        # init state for a already completed block
        old_highest_confirmed_id = 100
        old_highest_block_id = 200
        old_block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
        old_run_created_ts = state_manager.get_run_created_ts(hoster_prefix=HOSTER_PREFIX)
        state_manager.set_highest_confirmed_repo_id(hoster_prefix=HOSTER_PREFIX, repo_id=old_highest_confirmed_id)
        state_manager.set_highest_block_repo_id(hoster_prefix=HOSTER_PREFIX, repo_id=old_highest_block_id)
        state_manager.reset(hoster_prefix=HOSTER_PREFIX)
        new_block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)

        # test that our setup took effect (old block is gone, only new one left)
        new_highest_confirmed_id = state_manager.get_highest_confirmed_repo_id(hoster_prefix=HOSTER_PREFIX)
        new_highest_block_id = state_manager.get_highest_block_repo_id(hoster_prefix=HOSTER_PREFIX)
        new_run_created_ts = state_manager.get_run_created_ts(hoster_prefix=HOSTER_PREFIX)
        new_blocks = state_manager.get_blocks(hoster_prefix=HOSTER_PREFIX)
        assert new_highest_confirmed_id != old_highest_confirmed_id
        assert new_highest_block_id != old_highest_block_id
        assert new_run_created_ts > old_run_created_ts
        assert len(new_blocks) == 1
        assert old_block.uid not in new_blocks
        assert new_block.uid in new_blocks


class TestRedisStateManager(TestLocalStateManager):
    @pytest.fixture()
    def state_manager(self, test_app):
        manager = RedisStateManager()
        manager.redis = redislite.Redis()
        yield manager
        manager.reset(hoster_prefix=HOSTER_PREFIX)
