from hubgrep_indexer.models.repositories.abstract_repository import Repository
from hubgrep_indexer.lib.block_helpers import get_block_for_crawler


class TestAddRepos:
    def _add_repos(self, test_app, hosting_service, route):
        """
        Add repos connected to a hosting_service
        """
        response = test_app.test_client().put(route, json=mock_github_repos)
        repo_class = Repository.repo_class_for_type(hosting_service.type)
        new_repos = repo_class.query.all()
        assert response.status == "200 OK"
        assert len(new_repos) == len(mock_github_repos)
        for i in range(len(mock_github_repos)):
            assert new_repos[i].name == mock_github_repos[i]["name"]
            assert new_repos[i].url == mock_github_repos[i]["url"]
            assert new_repos[i].owner_login == mock_github_repos[i]["owner"]["login"]

    def test_add_repos_auth(self, test_app, test_client, hosting_service):
        test_app.config["LOGIN_DISABLED"] = False
        with test_app.app_context():
            response = test_app.test_client().put(f"/api/v1/hosters/{hosting_service.id}/")
            assert response.status == "401 UNAUTHORIZED"

    def test_put_github_repos(self, test_app, hosting_service):
        """
        Add repos connected to a hosting_service
        """
        with test_app.app_context():
            self._add_repos(test_app,
                            hosting_service,
                            f"/api/v1/hosters/{hosting_service.id}/")

    def test_put_add_github_block_repos(self, test_app, hosting_service):
        """
        Get a block, attempt to add repos to according to that block
        """
        with test_app.app_context():
            block = get_block_for_crawler(hoster_id=hosting_service.id)
            self._add_repos(test_app,
                            hosting_service,
                            f"/api/v1/hosters/{hosting_service.id}/{block['uid']}")


mock_github_repos = [
    {
        "id": "MDEwOlJlcG9zaXRvcnkx",
        "name": "mockrepo",
        "nameWithOwner": "repomock/mockrepo",
        "homepageUrl": None,
        "url": "https://github.com/repomock/mockrepo",
        "createdAt": "2010-03-09T05:10:10Z",
        "updatedAt": "2010-03-09T16:57:19Z",
        "pushedAt": "2010-03-09T16:57:19Z",
        "shortDescriptionHTML": "",
        "description": None,
        "isArchived": False,
        "isPrivate": False,
        "isFork": False,
        "isEmpty": False,
        "isDisabled": False,
        "isLocked": False,
        "isTemplate": False,
        "stargazerCount": 0,
        "forkCount": 0,
        "diskUsage": 192,
        "owner": {
            "login": "repomock",
            "id": "MDQ6VXNlcjA=",
            "url": "https://github.com/repomock"
        },
        "repositoryTopics": {
            "nodes": []
        },
        "primaryLanguage": {
            "name": "Python"
        },
        "licenseInfo": {
            "name": "GNU General Public License v2.0",
            "nickname": "GNU GPLv2"
        }
    },
    {
        "id": "MDEwOlJlcG9zaXRvcnky",
        "name": "mockrepo2",
        "nameWithOwner": "repomock2/mockrepo2",
        "homepageUrl": None,
        "url": "https://github.com/repomock/mockrepo2",
        "createdAt": "2010-03-09T05:10:10Z",
        "updatedAt": "2010-03-09T16:57:19Z",
        "pushedAt": "2010-03-09T16:57:19Z",
        "shortDescriptionHTML": "",
        "description": None,
        "isArchived": False,
        "isPrivate": False,
        "isFork": False,
        "isEmpty": False,
        "isDisabled": False,
        "isLocked": False,
        "isTemplate": False,
        "stargazerCount": 0,
        "forkCount": 0,
        "diskUsage": 192,
        "owner": {
            "login": "repomock2",
            "id": "MDQ6VXNlcjE=",
            "url": "https://github.com/repomock2"
        },
        "repositoryTopics": {
            "nodes": []
        },
        "primaryLanguage": {
            "name": "Python"
        },
        "licenseInfo": {
            "name": "GNU General Public License v2.0",
            "nickname": "GNU GPLv2"
        }
    }
]
