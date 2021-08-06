import time
import pytest

from hubgrep_indexer.constants import CRAWLER_HEADER_MACHINE_ID
from hubgrep_indexer.lib.state_manager.abstract_state_manager import (
    AbstractStateManager,
)
from hubgrep_indexer.lib.block_helpers import (
    get_block_for_crawler,
    get_loadbalanced_block_for_crawler,
    resolve_api_key,
)
from tests.conftest import _add_hosting_service
from tests.helpers import HOSTER_TYPES


class TestBlockHelpers:
    @pytest.mark.parametrize(
        'hosting_service',  # matched against hosting_service fixture in conftest.py
        HOSTER_TYPES,
        indirect=True
    )
    def test_get_block_for_crawler(self, test_client, hosting_service):
        with test_client:
            block_dict = get_block_for_crawler(hosting_service.id)
            assert block_dict["hosting_service"]
            assert block_dict["callback_url"]

    @pytest.mark.parametrize(
        'hosting_service',  # matched against hosting_service fixture in conftest.py
        HOSTER_TYPES,
        indirect=True
    )
    def test_get_loadbalanced_block_simple(self, test_client, hosting_service):
        """
        a simple test if this thing returns anything
        (only one hoster added)
        """
        with test_client:
            # new state manager, only one hoster.
            # since the run_created_ts defaults to 0, we have a hosting service
            # we need to crawl!
            state_manager: AbstractStateManager
            block_dict = get_loadbalanced_block_for_crawler(hosting_service.type)
            assert block_dict["hosting_service"]
            assert block_dict['callback_url']

    @pytest.mark.parametrize("hoster_type", HOSTER_TYPES)
    def test_get_loadbalanced_block(self, test_client, test_state_manager, hoster_type):
        """
        register two hosting_services, test load balancing

        see comment in get_loadbalanced_block: the behavior is a bit odd,
        so the test has to be adjusted
        """
        with test_client:
            # we create two hosters, and explicitly set one to a very low 
            # timestamp, so it needs to be crawled,
            # and one to "now", so it has its timeout
            timed_out_hosting_service = _add_hosting_service(
                api_url=f"https://test_{hoster_type}_1.com/",
                landingpage_url="www.land1.com",
                type=hoster_type
            )
            recent_hosting_service = _add_hosting_service(
                api_url=f"https://test_{hoster_type}_2.com/",
                landingpage_url="www.land2.com",
                type=hoster_type
            )

            test_state_manager.set_run_created_ts(timed_out_hosting_service.id, 0)
            test_state_manager.set_run_created_ts(recent_hosting_service.id, time.time())

            block_dict = get_loadbalanced_block_for_crawler(hoster_type)
            assert block_dict["hosting_service"]["id"] == timed_out_hosting_service.id

    @pytest.mark.parametrize(
        'hosting_service',
        HOSTER_TYPES,
        indirect=True
    )
    def test_resolve_api_key(self, test_app, hosting_service):
        """
        Test that an api_key is resolved correctly.
        Test that an active api_key is not given out to additional crawlers (machine_ids).

        Note: relies on "hosting_service" fixture to set exactly ONE api_key per hosting_service.
        """
        # initially assign the key to machine id nr.1
        with test_app.test_request_context('/irrelevant/route', headers={CRAWLER_HEADER_MACHINE_ID: "test_id_1"}):
            api_key_1 = resolve_api_key(hosting_service=hosting_service)
            assert api_key_1 is not None
            assert api_key_1 == hosting_service.api_keys[0]

        # make sure that machine id nr.2 crawling the same hosting_service cannot retrieve the same key
        with test_app.test_request_context('/irrelevant/route', headers={CRAWLER_HEADER_MACHINE_ID: "test_id_2"}):
            api_key_2 = resolve_api_key(hosting_service=hosting_service)
            assert api_key_2 is not api_key_1
            assert api_key_2 is None

