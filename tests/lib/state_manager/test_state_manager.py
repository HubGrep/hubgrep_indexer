import redislite
import logging
import time

import redis
import pytest

from hubgrep_indexer.lib.state_manager.abstract_state_manager import LocalStateManager
from hubgrep_indexer.lib.state_manager.redis_state_manager import RedisStateManager


hoster = "hoster_1"


class TestLocalStateManager:
    @pytest.fixture()
    def state_manager(self):
        manager = LocalStateManager()
        yield manager
        manager.reset(hoster)

    def test_set_get_highest_repo_id(self, state_manager: LocalStateManager):
        assert state_manager.get_highest_block_repo_id(hoster) == 0
        state_manager.set_highest_block_repo_id(hoster, 1)
        assert state_manager.get_highest_block_repo_id(hoster) == 1
        state_manager.set_highest_block_repo_id(hoster, 0)
        assert state_manager.get_highest_block_repo_id(hoster) == 0

    def test_get_next_block(self, state_manager: LocalStateManager):
        # to_id should be batch_size for the first block
        hoster = "hoster_1"
        block = state_manager.get_next_block(hoster)
        assert block.from_id == 1
        assert block.to_id == state_manager.batch_size

        # second block should start at end of first block+1
        block = state_manager.get_next_block(hoster)
        assert block.from_id == state_manager.batch_size + 1

    def test_get_timed_out_block(self, state_manager: LocalStateManager):
        hoster = "hoster_1"
        block = state_manager.get_next_block(hoster)
        block_timeout = block.attempts_at[0] + state_manager.block_timeout + 1
        timed_out_block = state_manager.get_timed_out_block(
            hoster, timestamp_now=block_timeout
        )

        assert block.uid == timed_out_block.uid

    def test_delete_block(self, state_manager: LocalStateManager):
        hoster = "hoster_1"
        block = state_manager.get_next_block(hoster)
        assert len(state_manager.get_blocks(hoster).keys()) == 1
        state_manager._delete_block(hoster, block.uid)
        assert len(state_manager.get_blocks(hoster).keys()) == 0

    def test_run_uid(self, state_manager: LocalStateManager):
        hoster = "hoster_1"
        initial_run_uid = state_manager.get_run_uid(hoster)
        state_manager.reset(hoster)
        second_run_uid = state_manager.get_run_uid(hoster)
        assert initial_run_uid
        assert second_run_uid
        assert initial_run_uid != second_run_uid

    def test_empty_results_counter(self, state_manager: LocalStateManager):
        hoster = "hoster_1"
        new_count = 1
        initial_counter_state = state_manager.get_empty_results_counter(hoster_prefix=hoster)
        state_manager.set_empty_results_counter(hoster_prefix=hoster, count=new_count)
        second_counter_state = state_manager.get_empty_results_counter(hoster_prefix=hoster)
        assert initial_counter_state == 0
        assert second_counter_state == new_count



class TestRedisStateManager(TestLocalStateManager):
    @pytest.fixture()
    def state_manager(self, test_app):
        manager = RedisStateManager()
        manager.redis = redislite.Redis()
        yield manager
        manager.reset(hoster)
