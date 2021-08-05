import time
import pytest

from hubgrep_indexer.lib.state_manager.abstract_state_manager import (
    AbstractStateManager,
)
from hubgrep_indexer.lib.block_helpers import (
    get_block_for_crawler,
    get_loadbalanced_block_for_crawler,
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
