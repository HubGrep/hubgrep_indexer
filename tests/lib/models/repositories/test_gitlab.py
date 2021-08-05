import pytest
from hubgrep_indexer.models.repositories.gitlab import GitlabRepository
from hubgrep_indexer import db
from hubgrep_indexer.constants import HOST_TYPE_GITLAB
from tests.helpers import get_mock_repos


class TestGiteaRepository:
    @pytest.mark.parametrize(
        'hosting_service',  # matched against hosting_service fixture in conftest.py
        [HOST_TYPE_GITLAB],
        indirect=True
    )
    def test_add_from_dict(self, test_app, test_client, hosting_service):
        with test_app.app_context():
            mock_repos = get_mock_repos(hosting_service_type=hosting_service.type)
            repo = GitlabRepository.from_dict(hosting_service.id, mock_repos[0])
            db.session.add(repo)
            db.session.commit()

            assert GitlabRepository.query.count() == 1
            assert repo.name == mock_repos[0]["name"]


    # cannot test this on sqlite, since the copy function is a psycopg thing :(
    """
    def test_export_to_file(self, test_app, test_client, hosting_service):
        import tempfile
        import os
        import shutil
        import pathlib

        with test_app.app_context():
            repo = GiteaRepository.from_dict(hosting_service.id, gitea_results[0])
            db.session.add(repo)
            db.session.commit()
            filename = "testfile"
            with tempfile.TemporaryDirectory() as tempdir:
                GiteaRepository.export_csv_gz(
                    hosting_service.id,
                    hosting_service.type,
                    filename,
                    results_base_path=tempdir,
                )
                filepath = pathlib.Path(tempdir).joinpath(filename)
                assert filepath.stat().st_size != 0
    """
