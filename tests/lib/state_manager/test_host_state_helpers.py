import logging
import pytest

from hubgrep_indexer.api_blueprint.add_repos import _append_repos
from hubgrep_indexer.constants import (
    HOST_TYPE_GITHUB,
    HOST_TYPE_GITLAB,
    HOST_TYPE_GITEA,
)
from hubgrep_indexer.lib.block_helpers import get_block_for_crawler
from hubgrep_indexer.lib.state_manager.host_state_helpers import get_state_helper
from hubgrep_indexer.models.hosting_service import HostingService
from tests.helpers import route_put_repos, get_mock_repos, HOSTER_TYPES
from hubgrep_indexer import state_manager

logger = logging.getLogger(__name__)


class TestHostStateHelpers:
    @pytest.mark.parametrize(
        'hosting_service',
        HOSTER_TYPES,
        indirect=True
    )
    def test_state_helpers_has_reached_end_empty(
            self, test_client, hosting_service
    ):
        with test_client:
            # init state for a already completed block
            old_block = state_manager.get_next_block(hoster_prefix=hosting_service.id)
            state_manager.set_highest_confirmed_block_repo_id(
                hoster_prefix=hosting_service.id, repo_id=old_block.to_id
            )
            print("OLD?", state_manager.get_highest_confirmed_block_repo_id(hosting_service.id), old_block.to_id)
            state_manager.finish_block(hoster_prefix=hosting_service.id, block_uid=old_block.uid)
            print("OLD?", state_manager.get_highest_confirmed_block_repo_id(hosting_service.id), old_block.to_id)

            repos = []  # we're testing against what happens when we receive empty results
            new_block = state_manager.get_next_block(hosting_service.id)
            print("NEW?", state_manager.get_highest_confirmed_block_repo_id(hosting_service.id), new_block.to_id)

            state_helper = get_state_helper(hosting_service=hosting_service)

            has_reached_end = state_helper.has_reached_end(
                hosting_service=hosting_service,
                block=new_block,
                parsed_repos=repos,
            )
            if hosting_service.type == HOST_TYPE_GITHUB:
                # github should not assume end on single empty results
                assert has_reached_end is False
            else:
                assert has_reached_end is True

    @pytest.mark.parametrize(
        'hosting_service',  # matched against hosting_service fixture in conftest.py
        HOSTER_TYPES,
        indirect=True
    )
    def test_state_helpers_has_reached_end_using_db_and_and_routes(
            self, test_client, hosting_service: HostingService
    ):
        with test_client:
            print(f"testing for: {hosting_service.api_url} {hosting_service.id}")
            first_block = get_block_for_crawler(hosting_service_id=hosting_service.id)
            assert first_block
            route_put_repos(test_client=test_client,
                            hosting_service=hosting_service,
                            route=f"/api/v1/hosters/{hosting_service.id}/{first_block['uid']}",
                            repos=get_mock_repos(hosting_service_type=hosting_service.type))

            repos = []  # we're testing against what happens when we receive empty results, after
            _append_repos(hosting_service=hosting_service, repo_dicts=repos)
            new_block = get_block_for_crawler(hosting_service_id=hosting_service.id)
            assert new_block
            new_block = state_manager.get_block(hoster_prefix=hosting_service.id, block_uid=new_block["uid"])
            assert new_block

            state_helper = get_state_helper(hosting_service=hosting_service)

            has_reached_end = state_helper.has_reached_end(
                hosting_service=hosting_service,
                block=new_block,
                parsed_repos=repos,
            )
            if hosting_service.type == HOST_TYPE_GITHUB:
                # github should not assume end on single empty results
                assert has_reached_end is False
            else:
                assert has_reached_end is True

    @pytest.mark.parametrize(
        'hosting_service',
        HOSTER_TYPES,
        indirect=True
    )
    def test_state_helpers_too_many_consecutive_empty(
            self, hosting_service
    ):
        state_helper = get_state_helper(hosting_service=hosting_service)
        state_manager.set_empty_results_counter(
            hoster_prefix=hosting_service.id, count=state_helper.empty_results_max
        )
        has_too_many = state_helper.has_too_many_consecutive_empty_results(hosting_service=hosting_service)
        assert has_too_many is True

    @pytest.mark.parametrize(
        'hosting_service',
        HOSTER_TYPES,
        indirect=True
    )
    def test_state_helpers_resolve_state_continue(
            self, test_client, hosting_service
    ):
        with test_client:
            old_block = state_manager.get_next_block(hoster_prefix=hosting_service.id)
            state_helper = get_state_helper(hosting_service=hosting_service)
            repos = [
                {"id": id} for id in range(state_manager.batch_size)
            ]  # repos found by crawling the "old_block"
            state_helper.resolve_state(
                hosting_service=hosting_service,
                block_uid=old_block.uid,
                parsed_repos=repos,
            )

            new_block = state_manager.get_next_block(
                hoster_prefix=hosting_service.id
            )  # consider this awaiting results still
            new_run_created_ts = state_manager.get_run_created_ts(
                hoster_prefix=hosting_service.id
            )
            new_highest_confirmed_id = state_manager.get_highest_confirmed_block_repo_id(
                hoster_prefix=hosting_service.id
            )
            new_highest_block_id = state_manager.get_highest_block_repo_id(
                hoster_prefix=hosting_service.id
            )
            blocks = state_manager.get_blocks_dict(hoster_prefix=hosting_service.id)
            assert len(blocks) == 1
            assert new_block.uid in blocks
            assert old_block.uid not in blocks
            assert new_run_created_ts == old_block.run_created_ts
            assert new_run_created_ts == new_block.run_created_ts
            assert new_highest_confirmed_id == state_manager.batch_size
            assert new_highest_block_id == state_manager.batch_size * 2

    @pytest.mark.parametrize(
        'hosting_service',
        HOSTER_TYPES,
        indirect=True
    )
    def test_state_helpers_resolve_state_reset(
            self, test_client, hosting_service
    ):
        with test_client:
            # init with an old block state (attempt to raise side-effects to fail this test, if we introduce them)
            old_block = state_manager.get_next_block(hoster_prefix=hosting_service.id)
            state_manager.set_highest_confirmed_block_repo_id(
                hoster_prefix=hosting_service.id, repo_id=old_block.to_id
            )
            state_manager.finish_block(hoster_prefix=hosting_service.id, block_uid=old_block.uid)
            new_block = state_manager.get_next_block(hoster_prefix=hosting_service.id)

            state_helper = get_state_helper(hosting_service=hosting_service)
            if hosting_service.type == HOST_TYPE_GITHUB:
                # making sure that github resolves into state-reset as well
                state_manager.set_empty_results_counter(
                    hoster_prefix=hosting_service.id, count=state_helper.empty_results_max - 1
                )

            repos = []
            state_helper.resolve_state(
                hosting_service=hosting_service,
                block_uid=new_block.uid,
                parsed_repos=repos,
            )

            blocks = state_manager.get_blocks_list(hoster_prefix=hosting_service.id)

            # call next block to trigger next run, setting up the timestamp
            state_manager.get_next_block(hosting_service.id)

            new_run_created_ts = state_manager.get_run_created_ts(
                hoster_prefix=hosting_service.id
            )
            assert len(blocks) == 0
            assert new_run_created_ts != old_block.run_created_ts

    @pytest.mark.parametrize(
        'hosting_service',
        HOSTER_TYPES,
        indirect=True
    )
    def test_state_helpers_multiple_runs(
            self, test_client, hosting_service
    ):
        with test_client:
            state_helper = get_state_helper(hosting_service=hosting_service)
            id_start = state_manager.batch_size

            def resolve(_block_uid, _repos):
                state_helper.resolve_state(
                    hosting_service=hosting_service,
                    block_uid=_block_uid,
                    parsed_repos=_repos,
                )

            runs = 10
            run_created_ats = []
            for run_nr in range(runs):
                print(f"run {run_nr}")
                # get some results
                first_block = state_manager.get_next_block(hoster_prefix=hosting_service.id)
                first_id = id_start * run_nr + 1
                last_id = id_start * (run_nr + 1) + 1
                repos = [{"id": id} for id in range(first_id, last_id)]

                # append timestamp for this new run
                run_created_ats.append(
                    state_manager.get_run_created_ts(hoster_prefix=hosting_service.id)
                )

                resolve(first_block.uid, repos)

                # fake empty result to end the round
                second_block = state_manager.get_next_block(hoster_prefix=hosting_service.id)
                repos = []

                # special handling for github
                if hosting_service.type == HOST_TYPE_GITHUB:
                    # making sure that github resolves into state-reset as well
                    state_manager.set_empty_results_counter(
                        hoster_prefix=hosting_service.id,
                        count=state_helper.empty_results_max - 1,
                    )
                resolve(second_block.uid, repos)

            second_last_block = state_manager.get_next_block(hoster_prefix=hosting_service.id)
            last_block = state_manager.get_next_block(hoster_prefix=hosting_service.id)

            # get_next_block triggered a new run with a new timestamp
            # after the empty results in the loop
            run_created_ats.append(
                state_manager.get_run_created_ts(hoster_prefix=hosting_service.id)
            )

            assert len(run_created_ats) == runs + 1
            assert len(set(run_created_ats)) == runs + 1  # remove duplicates
            assert (
                    len(state_manager.get_blocks_list(hoster_prefix=hosting_service.id)) == 2
            )  # no blocks left in state

            assert second_last_block.from_id == 1
            assert second_last_block.to_id == id_start

            assert last_block.from_id == id_start + 1
            assert last_block.to_id == id_start * 2
