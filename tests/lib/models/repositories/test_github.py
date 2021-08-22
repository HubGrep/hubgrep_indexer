import pytest
from hubgrep_indexer.models.repositories.github import GithubRepository
from hubgrep_indexer import db
from hubgrep_indexer.constants import HOST_TYPE_GITHUB
from tests.helpers import get_mock_repos


class TestGithubRepository:
    def test_clean_string(self):
        assert GithubRepository.clean_string("\x00test") == "\uFFFDtest"
        assert GithubRepository.clean_string(None) is None
        assert GithubRepository.clean_string("test") == "test"
