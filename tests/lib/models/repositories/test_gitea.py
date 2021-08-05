import pytest
import time
import logging
from hubgrep_indexer.models.repositories.gitea import GiteaRepository
from hubgrep_indexer import db
from hubgrep_indexer.constants import HOST_TYPE_GITEA
from tests.helpers import get_mock_repos
from hubgrep_indexer.api_blueprint.add_repos import _append_repos

logger = logging.getLogger(__name__)

class TestGiteaRepository:
    @pytest.mark.parametrize(
        'hosting_service',  # matched against hosting_service fixture in conftest.py
        [HOST_TYPE_GITEA],
        indirect=True
    )
    def test_add_from_dict(self, test_app, test_client, hosting_service):
        with test_app.app_context():
            mock_repos = get_mock_repos(hosting_service_type=hosting_service.type)
            repo = GiteaRepository.from_dict(hosting_service.id, mock_repos[0])
            db.session.add(repo)
            db.session.commit()

            assert GiteaRepository.query.count() == 1
            assert repo.name == mock_repos[0]["name"]

    @pytest.mark.parametrize(
        'hosting_service',  # matched against hosting_service fixture in conftest.py
        [HOST_TYPE_GITEA],
        indirect=True
    )
    def test_rotate(self, test_app, test_client, hosting_service):
        mock_repos = get_mock_repos(hosting_service_type=hosting_service.type)
        repo = GiteaRepository.from_dict(hosting_service.id, mock_repos[0])
        db.session.add(repo)
        db.session.commit()
        # we added a repo
        assert GiteaRepository.query.count() == 1

        # rotating should delete repos from past runs (none so far) 
        GiteaRepository.rotate(hosting_service)
        assert GiteaRepository.query.count() == 1

        mock_repos = get_mock_repos(hosting_service_type=hosting_service.type)
        repo = GiteaRepository.from_dict(hosting_service.id, mock_repos[0])
        db.session.add(repo)
        db.session.commit()
        
        assert GiteaRepository.query.count() == 2
        # rotate deletes the last run, leaving only the newest repo
        GiteaRepository.rotate(hosting_service)
        assert GiteaRepository.query.count() == 1

    @pytest.mark.parametrize(
        'hosting_service',  # matched against hosting_service fixture in conftest.py
        [HOST_TYPE_GITEA],
        indirect=True
    )
    def test_tmp_table(self, test_app, test_client, hosting_service):
        mock_repos = []
        repo_blocks = 1
        for _ in range(repo_blocks):
            for _ in range(1000):
                mock_repos += get_mock_repos(hosting_service_type=hosting_service.type)
            _append_repos(hosting_service, mock_repos)
            
        before = time.time()
        with GiteaRepository.make_tmp_table(hosting_service) as table_name:
            logger.debug(f"making tmp table for {len(mock_repos)} repos took {time.time() - before}")
            assert table_name

