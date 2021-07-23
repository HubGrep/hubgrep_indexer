import time

from hubgrep_indexer.lib.state_manager.abstract_state_manager import (
    AbstractStateManager,
)
from hubgrep_indexer.lib.block_helpers import (
    get_block_for_crawler,
    get_loadbalanced_block_for_crawler,
)


class TestBlockHelpers:
    def test_get_block_for_crawler(self, test_app, hosting_service_github_1):
        with test_app.app_context() as app:
            block_dict = get_block_for_crawler(hosting_service_github_1.id)
            assert block_dict["crawler"]
            assert block_dict["callback_url"]

    def test_get_loadbalanced_block_simple(self, test_app, hosting_service_github_1):
        """
        a simple test if this thing returns anything
        (only one hoster added)
        """
        with test_app.app_context() as app:
            # new state manager, only one hoster.
            # since the run_created_ts defaults to 0, we have a hosting service
            # we need to crawl!
            block_dict = get_loadbalanced_block_for_crawler(hosting_service_github_1.type)
            assert block_dict["crawler"]
            assert block_dict['callback_url']

    def test_get_loadbalanced_block(self, test_app, test_state_manager, hosting_service_github_1, hosting_service_github_2):
        """
        register two hosting_services, test load balancing

        see comment in get_loadbalanced_block: the behavior is a bit odd,
        so the test has to be adjusted
        """
        with test_app.app_context() as app:
            # we create two hosters, and explicitly set one to a very low 
            # timestamp, so it needs to be crawled,
            # and one to "now", so it has its timeout
            timed_out_hosting_service = hosting_service_github_1
            recent_hosting_service = hosting_service_github_2

            test_state_manager.set_run_created_ts(timed_out_hosting_service.id, 0)
            test_state_manager.set_run_created_ts(recent_hosting_service.id, time.time())

            block_dict = get_loadbalanced_block_for_crawler(hosting_service_github_1.type)
            assert block_dict["crawler"]["id"] == timed_out_hosting_service.id
