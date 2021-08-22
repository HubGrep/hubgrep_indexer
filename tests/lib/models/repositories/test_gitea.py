import pytest
import time
import logging
from hubgrep_indexer.models.repositories.gitea import GiteaRepository
from hubgrep_indexer.lib.table_helper import TableHelper
from hubgrep_indexer import db
from hubgrep_indexer.constants import HOST_TYPE_GITEA
from tests.helpers import get_mock_repos
from hubgrep_indexer.api_blueprint.add_repos import _append_repos

logger = logging.getLogger(__name__)


class TestGiteaRepository:
    @pytest.mark.parametrize(
        "hosting_service",  # matched against hosting_service fixture in conftest.py
        [HOST_TYPE_GITEA],
        indirect=True,
    )
    def test_add_from_dict(self, test_app, test_client, hosting_service):
        with test_app.app_context():
            mock_repos = get_mock_repos(hosting_service_type=hosting_service.type)
            repo = GiteaRepository.from_dict(hosting_service.id, mock_repos[0])
            db.session.add(repo)
            db.session.commit()

            assert GiteaRepository.query.count() == 1
            assert repo.name == mock_repos[0]["name"]

