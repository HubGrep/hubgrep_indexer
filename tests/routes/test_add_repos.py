from hubgrep_indexer.lib.block_helpers import get_block_for_crawler
from tests.helpers import route_put_add_repos, get_mock_repos


class TestAddRepos:
    def test_add_repos_auth(self, test_app, test_client, hosting_service_github_1):
        test_app.config["LOGIN_DISABLED"] = False
        with test_app.app_context():
            response = test_app.test_client().put(f"/api/v1/hosters/{hosting_service_github_1.id}/")
            assert response.status == "401 UNAUTHORIZED"

    def test_put_github_repos(self, test_app, hosting_service_github_1):
        """
        Add repos connected to a hosting_service
        """
        with test_app.app_context():
            route_put_add_repos(test_app,
                                hosting_service=hosting_service_github_1,
                                route=f"/api/v1/hosters/{hosting_service_github_1.id}/",
                                repos=get_mock_repos(hosting_service_type=hosting_service_github_1.type))

    def test_put_add_github_block_repos(self, test_app, hosting_service_github_1):
        """
        Get a block, attempt to add repos to according to that block
        """
        with test_app.app_context():
            block_1 = get_block_for_crawler(hosting_service_id=hosting_service_github_1.id)
            route_put_add_repos(test_app,
                                hosting_service=hosting_service_github_1,
                                route=f"/api/v1/hosters/{hosting_service_github_1.id}/{block_1['uid']}",
                                repos=get_mock_repos(hosting_service_type=hosting_service_github_1.type))
