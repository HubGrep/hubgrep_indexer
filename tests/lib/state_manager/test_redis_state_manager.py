import pytest
import time
from multiprocessing import Process

from hubgrep_indexer.lib.state_manager.abstract_state_manager import AbstractStateManager
from tests.helpers import HOSTER_TYPES

HOSTER_PREFIX = "hoster_1"


class TestRedisStateManager:

    def test_set_get_highest_repo_id(self, test_state_manager: AbstractStateManager):
        assert test_state_manager.get_highest_block_repo_id(
            hoster_prefix=HOSTER_PREFIX) == 0
        test_state_manager.set_highest_block_repo_id(
            hoster_prefix=HOSTER_PREFIX, repo_id=1)
        assert test_state_manager.get_highest_block_repo_id(
            hoster_prefix=HOSTER_PREFIX) == 1
        test_state_manager.set_highest_block_repo_id(
            hoster_prefix=HOSTER_PREFIX, repo_id=0)
        assert test_state_manager.get_highest_block_repo_id(
            hoster_prefix=HOSTER_PREFIX) == 0

    def test_get_next_block(self, test_state_manager: AbstractStateManager):
        # to_id should be batch_size for the first block
        block = test_state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
        assert block.from_id == 1
        assert block.to_id == test_state_manager.batch_size

        # second block should start at end of first block+1
        block = test_state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
        assert block.from_id == test_state_manager.batch_size + 1

    def test_get_timed_out_block(self, test_state_manager: AbstractStateManager):
        block = test_state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
        block_timeout = block.attempts_at[0] + test_state_manager.block_timeout + 1
        timed_out_block = test_state_manager.get_timed_out_block(
            hoster_prefix=HOSTER_PREFIX, timestamp_now=block_timeout
        )

        assert block.uid == timed_out_block.uid

    def test_get_and_update_block(self, test_state_manager: AbstractStateManager):
        old_block = test_state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
        old_block.attempts_at.append("im an int timestamp, really!")
        test_state_manager.update_block(hoster_prefix=HOSTER_PREFIX, block=old_block)
        block = test_state_manager.get_block(hoster_prefix=HOSTER_PREFIX, block_uid=old_block.uid)

        assert block.attempts_at[-1] == old_block.attempts_at[-1]

    def test_delete_block(self, test_state_manager: AbstractStateManager):
        block = test_state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
        assert len(test_state_manager.get_blocks(
            hoster_prefix=HOSTER_PREFIX).keys()) == 1
        test_state_manager._delete_block(
            hoster_prefix=HOSTER_PREFIX, block_uid=block.uid)
        assert len(test_state_manager.get_blocks(
            hoster_prefix=HOSTER_PREFIX).keys()) == 0

    def test_finish_block(self, test_state_manager: AbstractStateManager):
        self.test_delete_block(test_state_manager=test_state_manager)

    def test_finish_run(self, test_state_manager: AbstractStateManager):
        created_ts = 11
        highest_confirmed_id = 40
        highest_block_id = 100
        test_state_manager.set_highest_block_repo_id(HOSTER_PREFIX, highest_block_id)
        test_state_manager.set_highest_confirmed_block_repo_id(HOSTER_PREFIX, highest_confirmed_id)
        test_state_manager.set_run_created_ts(HOSTER_PREFIX, created_ts)
        # False is implied
        # test_state_manager.set_run_is_finished(HOSTER_PREFIX, False)

        test_state_manager.finish_run(HOSTER_PREFIX)

        assert test_state_manager.get_highest_block_repo_id(HOSTER_PREFIX) == highest_block_id
        assert test_state_manager.get_highest_confirmed_block_repo_id(HOSTER_PREFIX) == highest_confirmed_id
        assert test_state_manager.get_run_created_ts(HOSTER_PREFIX) == created_ts
        assert test_state_manager.get_is_run_finished(HOSTER_PREFIX)

    def test_set_run_not_finished(self, test_state_manager: AbstractStateManager):
        test_state_manager.set_is_run_finished(HOSTER_PREFIX, False)
        assert not test_state_manager.get_is_run_finished(HOSTER_PREFIX)

    def test_run_created_ts(self, test_state_manager: AbstractStateManager):
        # create a ts for "now"
        test_state_manager.set_run_created_ts(HOSTER_PREFIX)
        initial_run_created_ts = test_state_manager.get_run_created_ts(
            hoster_prefix=HOSTER_PREFIX)

        # create another timestamp
        test_state_manager.set_run_created_ts(HOSTER_PREFIX, timestamp=11)
        second_run_created_ts = test_state_manager.get_run_created_ts(
            hoster_prefix=HOSTER_PREFIX)
        assert initial_run_created_ts
        assert second_run_created_ts == 11
        assert initial_run_created_ts != second_run_created_ts

    def test_empty_results_counter(self, test_state_manager: AbstractStateManager):
        new_count = 1
        initial_counter_state = test_state_manager.get_empty_results_counter(
            hoster_prefix=HOSTER_PREFIX)
        test_state_manager.set_empty_results_counter(
            hoster_prefix=HOSTER_PREFIX, count=new_count)
        second_counter_state = test_state_manager.get_empty_results_counter(
            hoster_prefix=HOSTER_PREFIX)
        assert initial_counter_state == 0
        assert second_counter_state == new_count

    def test_reset(self, test_state_manager: AbstractStateManager):
        # init state for a already completed block
        old_highest_confirmed_id = 100
        old_highest_block_id = 200
        old_block = test_state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
        old_run_created_ts = test_state_manager.get_run_created_ts(
            hoster_prefix=HOSTER_PREFIX)
        test_state_manager.set_highest_confirmed_block_repo_id(
            hoster_prefix=HOSTER_PREFIX, repo_id=old_highest_confirmed_id)
        test_state_manager.set_highest_block_repo_id(
            hoster_prefix=HOSTER_PREFIX, repo_id=old_highest_block_id)
        test_state_manager.reset(hoster_prefix=HOSTER_PREFIX)
        new_block = test_state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)

        # test that our setup took effect (old block is gone, only new one left)
        new_highest_confirmed_id = test_state_manager.get_highest_confirmed_block_repo_id(
            hoster_prefix=HOSTER_PREFIX)
        new_highest_block_id = test_state_manager.get_highest_block_repo_id(
            hoster_prefix=HOSTER_PREFIX)
        new_run_created_ts = test_state_manager.get_run_created_ts(
            hoster_prefix=HOSTER_PREFIX)
        new_blocks = test_state_manager.get_blocks(hoster_prefix=HOSTER_PREFIX)
        assert new_highest_confirmed_id != old_highest_confirmed_id
        assert new_highest_block_id != old_highest_block_id
        assert new_run_created_ts > old_run_created_ts
        assert len(new_blocks) == 1
        assert old_block.uid not in new_blocks
        assert new_block.uid in new_blocks

    @pytest.mark.timeout(5)
    def test_get_lock_is_blocking_1(self, test_state_manager):
        """
        We get a lock in a subprocess which waits before release, during this time we try to get a 2nd lock
        which should be blocking UNTIL the first lock has released.

        If it's not released we rely on a pytest timeout to fail the test for us.
        """

        def _get_lock(_state_manager, sleep_time: int):
            with _state_manager.get_lock(1):
                time.sleep(sleep_time)

        time_blocked = time.time()
        p = Process(target=_get_lock, args=(test_state_manager, 1))
        p.start()
        time.sleep(0.1)  # this is a bit finicky, delay slightly to end up executing BEHIND the subprocess
        _get_lock(test_state_manager, 0)
        time_blocked = time.time() - time_blocked
        assert time_blocked > .5

    def test_get_lock_is_blocking_2(self, test_state_manager):
        """
        a less fancy test, if the lock works

        """
        # get a lock, and aquire it
        with test_state_manager.get_lock(5):
            # get a second lock (unaquired)
            lock = test_state_manager.get_lock(5)
            # check if its locked, without using it
            # (should be locked here)
            assert lock.locked()

        # get a second one, should be unlocked now
        lock = test_state_manager.get_lock(5)
        assert not lock.locked()

    @pytest.mark.parametrize(
        'hosting_service',
        HOSTER_TYPES,
        indirect=True
    )
    def test_machine_api_key_states(self, test_state_manager, hosting_service):
        machine_id = "test_machine_id"
        api_key = "test_api_key"

        # is key NOT in use?
        assert not test_state_manager.is_api_key_active(hosting_service_id=hosting_service.id,
                                                        api_key=api_key)

        # is key NOW in use?
        test_state_manager.set_machine_api_key(hosting_service_id=hosting_service.id,
                                               machine_id=machine_id,
                                               api_key=api_key)
        assert test_state_manager.is_api_key_active(hosting_service_id=hosting_service.id,
                                                    api_key=api_key)

        # is it the ORIGINAL key?
        retrieved_api_key_1 = test_state_manager.get_machine_api_key(hosting_service_id=hosting_service.id,
                                                                     machine_id=machine_id)
        assert retrieved_api_key_1 == api_key

        # is it NOT in use after removal?
        test_state_manager.remove_machine_api_key(hosting_service_id=hosting_service.id,
                                                  api_key=api_key)
        assert not test_state_manager.is_api_key_active(hosting_service_id=hosting_service.id,
                                                        api_key=api_key)

        # can we STILL get it after removal?
        retrieved_api_key_2 = test_state_manager.get_machine_api_key(hosting_service_id=hosting_service.id,
                                                                     machine_id=machine_id)
        assert retrieved_api_key_2 is None
