import pytest
from hubgrep_indexer.models.repositories.github import GithubRepository
from hubgrep_indexer import db
from hubgrep_indexer.constants import HOST_TYPE_GITHUB
from tests.helpers import get_mock_repos


class TestGithubRepository:
    @pytest.mark.parametrize(
        'hosting_service',  # matched against hosting_service fixture in conftest.py
        [HOST_TYPE_GITHUB],
        indirect=True
    )
    def test_add_from_dict(self, test_app, test_client, hosting_service):
        with test_app.app_context():
            mock_repos = get_mock_repos(hosting_service_type=hosting_service.type)
            repo = GithubRepository.from_dict(hosting_service.id, mock_repos[0])
            db.session.add(repo)
            db.session.commit()

            assert GithubRepository.query.count() == 1
            assert repo.name == mock_repos[0]["name"]

    def test_clean_string(self):
        assert GithubRepository.clean_string("\x00test") == "\uFFFDtest"
        assert GithubRepository.clean_string(None) == None
        assert GithubRepository.clean_string("test") == "test"
