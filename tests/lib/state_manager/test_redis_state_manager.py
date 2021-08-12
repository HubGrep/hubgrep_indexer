import pytest
import time
from multiprocessing import Process

from hubgrep_indexer.lib.state_manager.abstract_state_manager import AbstractStateManager
from hubgrep_indexer import state_manager
from tests.helpers import HOSTER_TYPES

HOSTER_PREFIX = "hoster_1"


class TestRedisStateManager:

    def test_set_get_highest_repo_id(self):
        assert state_manager.get_highest_block_repo_id(
            hoster_prefix=HOSTER_PREFIX) == 0
        state_manager.set_highest_block_repo_id(
            hoster_prefix=HOSTER_PREFIX, repo_id=1)
        assert state_manager.get_highest_block_repo_id(
            hoster_prefix=HOSTER_PREFIX) == 1
        state_manager.set_highest_block_repo_id(
            hoster_prefix=HOSTER_PREFIX, repo_id=0)
        assert state_manager.get_highest_block_repo_id(
            hoster_prefix=HOSTER_PREFIX) == 0

    def test_get_next_block(self, test_client):
        with test_client:
            # to_id should be batch_size for the first block
            block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
            assert block.from_id == 1
            assert block.to_id == state_manager.batch_size

            # second block should start at end of first block+1
            block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
            assert block.from_id == state_manager.batch_size + 1

    def test_get_timed_out_block(self, test_client):
        with test_client:
            block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
            block_timeout = block.attempts_at[0] + state_manager.block_timeout + 1
            timed_out_block = state_manager.get_timed_out_block(
                hoster_prefix=HOSTER_PREFIX, timestamp_now=block_timeout
            )

            assert block.uid == timed_out_block.uid

    def test_get_and_update_block(self, test_client):
        with test_client:
            old_block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
            old_block.attempts_at.append("im an int timestamp, really!")
            state_manager.update_block(hoster_prefix=HOSTER_PREFIX, block=old_block)
            block = state_manager.get_block(hoster_prefix=HOSTER_PREFIX, block_uid=old_block.uid)

            assert block.attempts_at[-1] == old_block.attempts_at[-1]

    def test_delete_block(self, test_client):
        with test_client:
            block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
            assert len(state_manager.get_blocks_list(
                hoster_prefix=HOSTER_PREFIX)) == 1
            state_manager._delete_block(
                hoster_prefix=HOSTER_PREFIX, block_uid=block.uid)
            assert len(state_manager.get_blocks_list(
                hoster_prefix=HOSTER_PREFIX)) == 0

    def test_finish_block(self, test_client):
        self.test_delete_block(test_client=test_client)

    def test_finish_run(self):
        created_ts = 11
        highest_block_id = 100
        highest_confirmed_id = 40
        state_manager.set_highest_block_repo_id(HOSTER_PREFIX, highest_block_id)
        state_manager.set_highest_confirmed_block_repo_id(HOSTER_PREFIX, highest_confirmed_id)
        state_manager.set_run_created_ts(HOSTER_PREFIX, created_ts)
        # False is implied
        # state_manager.set_run_is_finished(HOSTER_PREFIX, False)

        state_manager.finish_run(HOSTER_PREFIX)

        assert state_manager.get_highest_block_repo_id(HOSTER_PREFIX) != highest_block_id
        assert state_manager.get_highest_confirmed_block_repo_id(HOSTER_PREFIX) != highest_confirmed_id
        assert state_manager.get_run_created_ts(HOSTER_PREFIX) != created_ts
        assert not state_manager.get_has_run_hit_end(HOSTER_PREFIX)

    def test_set_run_not_finished(self):
        state_manager.set_has_run_hit_end(HOSTER_PREFIX, False)
        assert not state_manager.get_has_run_hit_end(HOSTER_PREFIX)

    def test_run_created_ts(self):
        # create a ts for "now"
        state_manager.set_run_created_ts(HOSTER_PREFIX)
        initial_run_created_ts = state_manager.get_run_created_ts(
            hoster_prefix=HOSTER_PREFIX)

        # create another timestamp
        state_manager.set_run_created_ts(HOSTER_PREFIX, timestamp=11)
        second_run_created_ts = state_manager.get_run_created_ts(
            hoster_prefix=HOSTER_PREFIX)
        assert initial_run_created_ts
        assert second_run_created_ts == 11
        assert initial_run_created_ts != second_run_created_ts

    def test_empty_results_counter(self):
        new_count = 1
        initial_counter_state = state_manager.get_empty_results_counter(
            hoster_prefix=HOSTER_PREFIX)
        state_manager.set_empty_results_counter(
            hoster_prefix=HOSTER_PREFIX, count=new_count)
        second_counter_state = state_manager.get_empty_results_counter(
            hoster_prefix=HOSTER_PREFIX)
        assert initial_counter_state == 0
        assert second_counter_state == new_count

    def test_reset(self, test_client):
        with test_client:
            # init state for a already completed block
            old_highest_confirmed_id = 100
            old_highest_block_id = 200
            old_block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
            old_run_created_ts = state_manager.get_run_created_ts(
                hoster_prefix=HOSTER_PREFIX)
            state_manager.set_highest_confirmed_block_repo_id(
                hoster_prefix=HOSTER_PREFIX, repo_id=old_highest_confirmed_id)
            state_manager.set_highest_block_repo_id(
                hoster_prefix=HOSTER_PREFIX, repo_id=old_highest_block_id)
            state_manager.reset(hoster_prefix=HOSTER_PREFIX)
            new_block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)

            # test that our setup took effect (old block is gone, only new one left)
            new_highest_confirmed_id = state_manager.get_highest_confirmed_block_repo_id(
                hoster_prefix=HOSTER_PREFIX)
            new_highest_block_id = state_manager.get_highest_block_repo_id(
                hoster_prefix=HOSTER_PREFIX)
            new_run_created_ts = state_manager.get_run_created_ts(
                hoster_prefix=HOSTER_PREFIX)
            new_blocks = state_manager.get_blocks_dict(hoster_prefix=HOSTER_PREFIX)
            assert new_highest_confirmed_id != old_highest_confirmed_id
            assert new_highest_block_id != old_highest_block_id
            assert new_run_created_ts > old_run_created_ts
            assert len(new_blocks) == 1
            assert old_block.uid not in new_blocks
            assert new_block.uid in new_blocks

    @pytest.mark.timeout(5)
    def test_get_lock_is_blocking_1(self):
        """
        We get a lock in a subprocess which waits before release, during this time we try to get a 2nd lock
        which should be blocking UNTIL the first lock has released.

        If it's not released we rely on a pytest timeout to fail the test for us.
        """

        def _get_lock(_state_manager, sleep_time: int):
            with _state_manager.get_lock(1):
                time.sleep(sleep_time)

        time_blocked = time.time()
        p = Process(target=_get_lock, args=(state_manager, 1))
        p.start()
        time.sleep(0.1)  # this is a bit finicky, delay slightly to end up executing BEHIND the subprocess
        _get_lock(state_manager, 0)
        time_blocked = time.time() - time_blocked
        assert time_blocked > .5

    def test_get_lock_is_blocking_2(self):
        """
        a less fancy test, if the lock works

        """
        # get a lock, and aquire it
        with state_manager.get_lock(5):
            # get a second lock (unaquired)
            lock = state_manager.get_lock(5)
            # check if its locked, without using it
            # (should be locked here)
            assert lock.locked()

        # get a second one, should be unlocked now
        lock = state_manager.get_lock(5)
        assert not lock.locked()

    @pytest.mark.parametrize(
        'hosting_service',
        HOSTER_TYPES,
        indirect=True
    )
    def test_machine_api_key_states(self, hosting_service):
        machine_id = "test_machine_id"
        api_key = "test_api_key"

        # is key NOT in use?
        assert not state_manager.is_api_key_active(hosting_service_id=hosting_service.id,
                                                        api_key=api_key)

        # is key NOW in use?
        state_manager.set_machine_api_key(hosting_service_id=hosting_service.id,
                                               machine_id=machine_id,
                                               api_key=api_key)
        assert state_manager.is_api_key_active(hosting_service_id=hosting_service.id,
                                                    api_key=api_key)

        # is it the ORIGINAL key?
        retrieved_api_key_1 = state_manager.get_machine_api_key(hosting_service_id=hosting_service.id,
                                                                     machine_id=machine_id)
        assert retrieved_api_key_1 == api_key

        # is it NOT in use after removal?
        state_manager.remove_machine_api_key(hosting_service_id=hosting_service.id,
                                                  api_key=api_key)
        assert not state_manager.is_api_key_active(hosting_service_id=hosting_service.id,
                                                        api_key=api_key)

        # can we STILL get it after removal?
        retrieved_api_key_2 = state_manager.get_machine_api_key(hosting_service_id=hosting_service.id,
                                                                     machine_id=machine_id)
        assert retrieved_api_key_2 is None
