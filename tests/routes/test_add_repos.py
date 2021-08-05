from hubgrep_indexer.lib.block_helpers import get_block_for_crawler
from tests.helpers import route_put_add_repos, get_mock_repos


class TestAddRepos:
    def _add_repos(self, test_client, hosting_service, route):
        """
        Add repos connected to a hosting_service
        """
        mock_repos = get_mock_repos(hosting_service.type)
        response = test_client.put(route, json=mock_repos)
        repo_class = Repository.repo_class_for_type(hosting_service.type)
        new_repos = repo_class.query.all()
        assert response.status == "200 OK"
        assert len(new_repos) == len(mock_repos)
        for i in range(len(mock_repos)):
            assert new_repos[i].id == mock_repos[i]["id"]
            assert new_repos[i].name == mock_repos[i]["name"]

    def test_add_repos_auth(self, test_app, hosting_service):
        test_app.config["LOGIN_DISABLED"] = False
        with test_app.app_context():
            response = test_app.test_client().put(f"/api/v1/hosters/{hosting_service.id}/")
            assert response.status == "401 UNAUTHORIZED"

    def test_put_github_repos(self, test_client, hosting_service):
        """
        Add repos connected to a hosting_service
        """
        with test_client:
            self._add_repos(test_client,
                            hosting_service,
                            f"/api/v1/hosters/{hosting_service.id}/")

    def test_put_add_github_block_repos(self, test_client, hosting_service):
        """
        Get a block, attempt to add repos to according to that block
        """
        with test_client:
            block = get_block_for_crawler(hosting_service_id=hosting_service.id)
            self._add_repos(test_client,
                            hosting_service,
                            f"/api/v1/hosters/{hosting_service.id}/{block['uid']}")

