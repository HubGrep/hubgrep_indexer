import pytest

from hubgrep_indexer.lib.block_helpers import get_block_for_crawler
from tests.helpers import route_put_repos, get_mock_repos, HOSTER_TYPES


class TestAddRepos:

    @pytest.mark.parametrize(
        'hosting_service',  # matched against hosting_service fixture in conftest.py
        HOSTER_TYPES,
        indirect=True
    )
    def test_add_repos_auth(self, test_app, hosting_service):
        test_app.config["LOGIN_DISABLED"] = False
        with test_app.app_context():
            response = test_app.test_client().put(f"/api/v1/hosters/{hosting_service.id}/")
            assert response.status == "401 UNAUTHORIZED"

    @pytest.mark.parametrize(
        'hosting_service',
        HOSTER_TYPES,
        indirect=True
    )
    def test_put_repos(self, test_client, hosting_service):
        """
        Add repos connected to a hosting_service
        """
        with test_client:
            route_put_repos(test_client=test_client,
                            hosting_service=hosting_service,
                            route=f"/api/v1/hosters/{hosting_service.id}/",
                            repos=get_mock_repos(hosting_service_type=hosting_service.type))

    @pytest.mark.parametrize(
        'hosting_service',
        HOSTER_TYPES,
        indirect=True
    )
    def test_put_block_repos(self, test_client, hosting_service):
        """
        Get a block, attempt to add repos to according to that block
        """
        with test_client:
            block = get_block_for_crawler(hosting_service_id=hosting_service.id)
            route_put_repos(test_client=test_client,
                            hosting_service=hosting_service,
                            route=f"/api/v1/hosters/{hosting_service.id}/{block['uid']}",
                            repos=get_mock_repos(hosting_service_type=hosting_service.type))
