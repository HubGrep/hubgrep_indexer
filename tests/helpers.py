from hubgrep_indexer.models.hosting_service import HostingService
from hubgrep_indexer.models.repositories.abstract_repository import Repository
from hubgrep_indexer.constants import (
    HOST_TYPE_GITHUB,
    HOST_TYPE_GITLAB,
    HOST_TYPE_GITEA,
)
from tests.mock_repos import mock_github_repos, mock_gitea_repos, mock_gitlab_repos


HOSTER_TYPES = [HOST_TYPE_GITHUB, HOST_TYPE_GITLAB, HOST_TYPE_GITEA]
MOCK_REPOS = {
    HOST_TYPE_GITHUB: mock_github_repos,
    HOST_TYPE_GITLAB: mock_gitlab_repos,
    HOST_TYPE_GITEA: mock_gitea_repos
}


def get_mock_repos(hosting_service_type: str):
    return MOCK_REPOS[hosting_service_type]


def route_put_repos(test_client, hosting_service: HostingService, route: str, repos: list):
    """
    Add repos connected to a hosting_service (and assert that each repo has been inserted into DB).
    """
    response = test_client.put(route, json=repos)
    repo_class = Repository.repo_class_for_type(hosting_service.type)
    new_repos = repo_class.query.all()
    assert response.status == "200 OK"
    assert len(new_repos) == len(repos)
    for i in range(len(repos)):
        assert new_repos[i].name == repos[i]["name"]
