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
        assert state_manager.get_current_highest_repo_id(hoster) == 0
        state_manager.set_current_highest_repo_id(hoster, 1)
        assert state_manager.get_current_highest_repo_id(hoster) == 1
        state_manager.set_current_highest_repo_id(hoster, 0)
        assert state_manager.get_current_highest_repo_id(hoster) == 0

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


class TestRedisStateManager(TestLocalStateManager):
    @pytest.fixture()
    def state_manager(self, test_app):
        manager = RedisStateManager()
        manager.redis = redis.from_url(test_app.config['REDIS_URL'])
        yield manager
        manager.reset(hoster)
