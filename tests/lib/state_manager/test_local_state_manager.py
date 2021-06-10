from hubgrep_indexer.lib.state_manager.abstract_state_manager import LocalStateManager
import pytest
import time

import logging


class TestLocalStateManager:
    @pytest.fixture()
    def state_manager(self):
        logging.error("statemanager")
        return LocalStateManager()

    def test_set_get_highest_repo_id(self, state_manager: LocalStateManager):
        assert state_manager.current_highest_repo_id == 0
        state_manager.set_current_highest_repo_id(1)
        assert state_manager.current_highest_repo_id == 1
        assert state_manager.get_current_highest_repo_id() == 1
        state_manager.set_current_highest_repo_id(0)
        assert state_manager.current_highest_repo_id == 0
        assert state_manager.get_current_highest_repo_id() == 0

    def test_get_next_block(self, state_manager: LocalStateManager):
        block = state_manager.get_next_block()
        assert block.from_id == 1
        assert block.to_id == state_manager.batch_size

        block = state_manager.get_next_block()
        assert block.from_id == state_manager.batch_size + 1

    def test_get_timed_out_block(self, state_manager: LocalStateManager):
        block = state_manager.get_next_block()
        block_timeout = block.attempts_at[0] + state_manager.block_timeout + 1
        timed_out_block = state_manager.get_timed_out_block(timestamp_now=block_timeout)

        assert block.uid == timed_out_block.uid
