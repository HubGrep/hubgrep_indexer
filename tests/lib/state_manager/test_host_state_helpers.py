import pytest
import logging

logger = logging.getLogger(__name__)

from hubgrep_indexer.constants import (
    HOST_TYPE_GITHUB,
    HOST_TYPE_GITLAB,
    HOST_TYPE_GITEA,
)
from hubgrep_indexer.lib.state_manager.abstract_state_manager import (
    LocalStateManager,
    AbstractStateManager,
)
from hubgrep_indexer.lib.state_manager.host_state_helpers import get_state_helper

HOSTER_PREFIX = "hoster_1"
HOSTER_TYPES = [HOST_TYPE_GITHUB, HOST_TYPE_GITLAB, HOST_TYPE_GITEA]


class TestHostStateHelpers:
    @pytest.fixture()
    def state_manager(self):
        manager = LocalStateManager()
        yield manager
        manager.reset(HOSTER_PREFIX)

    @pytest.mark.parametrize("hoster_type", HOSTER_TYPES)
    def test_state_helpers_has_reached_end(
        self, hoster_type: str, state_manager: AbstractStateManager
    ):
        print(f"testing for: {hoster_type}")
        # init state for a already completed block
        old_block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
        state_manager.set_highest_confirmed_repo_id(
            hoster_prefix=HOSTER_PREFIX, repo_id=old_block.to_id
        )
        state_manager.finish_block(hoster_prefix=HOSTER_PREFIX, block_uid=old_block.uid)

        repos = []  # we're testing against what happens when we receive empty results
        new_block = state_manager.get_next_block(HOSTER_PREFIX)
        state_helper = get_state_helper(hoster_type)
        has_reached_end = state_helper.has_reached_end(
            hosting_service_id=HOSTER_PREFIX,
            state_manager=state_manager,
            block=new_block,
            parsed_repos=repos,
        )
        if hoster_type == HOST_TYPE_GITHUB:
            # github should not assume end on single empty results
            assert has_reached_end is False
        else:
            assert has_reached_end is True

    @pytest.mark.parametrize("hoster_type", HOSTER_TYPES)
    def test_state_helpers_too_many_consecutive_empty(
        self, hoster_type, state_manager: AbstractStateManager
    ):
        print(f"testing for: {hoster_type}")
        state_helper = get_state_helper(hoster_type)
        state_manager.set_empty_results_counter(
            hoster_prefix=HOSTER_PREFIX, count=state_helper.empty_results_max
        )
        has_too_many = state_helper.has_too_many_consecutive_empty_results(
            hosting_service_id=HOSTER_PREFIX, state_manager=state_manager
        )
        assert has_too_many is True

    @pytest.mark.parametrize("hoster_type", HOSTER_TYPES)
    def test_state_helpers_resolve_state_continue(
        self, hoster_type, state_manager: AbstractStateManager
    ):
        print(f"testing for: {hoster_type}")
        old_block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
        state_helper = get_state_helper(hoster_type)
        repos = [
            {"id": id} for id in range(state_manager.batch_size)
        ]  # repos found by crawling the "old_block"
        state_helper.resolve_state(
            hosting_service_id=HOSTER_PREFIX,
            state_manager=state_manager,
            block_uid=old_block.uid,
            parsed_repos=repos,
        )

        new_block = state_manager.get_next_block(
            hoster_prefix=HOSTER_PREFIX
        )  # consider this awaiting results still
        new_run_created_ts = state_manager.get_run_created_ts(
            hoster_prefix=HOSTER_PREFIX
        )
        new_highest_confirmed_id = state_manager.get_highest_confirmed_repo_id(
            hoster_prefix=HOSTER_PREFIX
        )
        new_highest_block_id = state_manager.get_highest_block_repo_id(
            hoster_prefix=HOSTER_PREFIX
        )
        blocks = state_manager.get_blocks(hoster_prefix=HOSTER_PREFIX)
        assert len(blocks) == 1
        assert new_block.uid in blocks
        assert old_block.uid not in blocks
        assert new_run_created_ts == old_block.run_created_ts
        assert new_run_created_ts == new_block.run_created_ts
        assert new_highest_confirmed_id == state_manager.batch_size
        assert new_highest_block_id == state_manager.batch_size * 2

    @pytest.mark.parametrize("hoster_type", HOSTER_TYPES)
    def test_state_helpers_resolve_state_reset(
        self, hoster_type, state_manager: AbstractStateManager
    ):
        print(f"testing for: {hoster_type}")
        # init with an old block state (attempt to raise side-effects to fail this test, if we introduce them)
        old_block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
        state_manager.set_highest_confirmed_repo_id(
            hoster_prefix=HOSTER_PREFIX, repo_id=old_block.to_id
        )
        state_manager.finish_block(hoster_prefix=HOSTER_PREFIX, block_uid=old_block.uid)
        new_block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)

        state_helper = get_state_helper(hoster_type)
        if hoster_type == HOST_TYPE_GITHUB:
            # making sure that github resolves into state-reset as well
            state_manager.set_empty_results_counter(
                hoster_prefix=HOSTER_PREFIX, count=state_helper.empty_results_max - 1
            )

        repos = []
        state_helper.resolve_state(
            hosting_service_id=HOSTER_PREFIX,
            state_manager=state_manager,
            block_uid=new_block.uid,
            parsed_repos=repos,
        )

        blocks = state_manager.get_blocks(hoster_prefix=HOSTER_PREFIX)

        # call next block to trigger next run, setting up the timestamp
        state_manager.get_next_block(HOSTER_PREFIX)

        new_run_created_ts = state_manager.get_run_created_ts(
            hoster_prefix=HOSTER_PREFIX
        )
        assert len(blocks) == 0
        assert new_run_created_ts != old_block.run_created_ts

    @pytest.mark.parametrize("hoster_type", HOSTER_TYPES)
    def test_state_helpers_multiple_runs(
        self, hoster_type, state_manager: AbstractStateManager
    ):
        print(f"testing for: {hoster_type}")
        state_helper = get_state_helper(hoster_type)
        id_start = state_manager.batch_size

        def resolve(_block_uid, _repos):
            state_helper.resolve_state(
                hosting_service_id=HOSTER_PREFIX,
                state_manager=state_manager,
                block_uid=_block_uid,
                parsed_repos=_repos,
            )

        runs = 10
        run_created_ats = []
        for run_nr in range(runs):
            logger.info(f"run {run_nr}")
            # get some results
            first_block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
            first_id = id_start * run_nr + 1
            last_id = id_start * (run_nr + 1) + 1
            repos = [{"id": id} for id in range(first_id, last_id)]

            # append timestamp for this new run
            run_created_ats.append(
                state_manager.get_run_created_ts(hoster_prefix=HOSTER_PREFIX)
            )

            resolve(first_block.uid, repos)

            # fake empty result to end the round
            second_block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
            repos = []

            # special handling for github
            if hoster_type == HOST_TYPE_GITHUB:
                # making sure that github resolves into state-reset as well
                state_manager.set_empty_results_counter(
                    hoster_prefix=HOSTER_PREFIX,
                    count=state_helper.empty_results_max - 1,
                )
            resolve(second_block.uid, repos)

        second_last_block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)
        last_block = state_manager.get_next_block(hoster_prefix=HOSTER_PREFIX)

        # get_next_block triggered a new run with a new timestamp
        # after the empty results in the loop
        run_created_ats.append(
            state_manager.get_run_created_ts(hoster_prefix=HOSTER_PREFIX)
        )

        assert len(run_created_ats) == runs + 1
        assert len(set(run_created_ats)) == runs + 1  # remove duplicates
        assert (
            len(state_manager.get_blocks(hoster_prefix=HOSTER_PREFIX)) == 2
        )  # no blocks left in state

        assert second_last_block.from_id == 1
        assert second_last_block.to_id == id_start

        assert last_block.from_id == id_start + 1
        assert last_block.to_id == id_start * 2
