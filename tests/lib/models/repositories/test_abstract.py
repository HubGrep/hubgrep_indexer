import pytest
import time
import logging
from hubgrep_indexer.models.repositories.abstract_repository import Repository
from hubgrep_indexer.lib.table_helper import TableHelper
from hubgrep_indexer import db
from hubgrep_indexer.constants import HOST_TYPE_GITEA, HOST_TYPE_GITHUB, HOST_TYPE_GITLAB
from tests.helpers import get_mock_repos
from hubgrep_indexer.api_blueprint.add_repos import _append_repos

logger = logging.getLogger(__name__)


class TestRepository:
    @pytest.mark.parametrize(
        "hosting_service",  # matched against hosting_service fixture in conftest.py
        [HOST_TYPE_GITEA, HOST_TYPE_GITHUB, HOST_TYPE_GITLAB],
        indirect=True,
    )
    def test_get_unification_sql(self, test_app, test_client, hosting_service):
        with test_app.app_context():
            repo_class = Repository.repo_class_for_type(hosting_service.type)
            select_sql = repo_class.get_unified_select_sql(hosting_service)
            assert select_sql

    @pytest.mark.parametrize(
        "hosting_service",  # matched against hosting_service fixture in conftest.py
        [HOST_TYPE_GITEA, HOST_TYPE_GITHUB, HOST_TYPE_GITLAB],
        indirect=True,
    )
    def test_unified_export(self, test_app, hosting_service):
        """
        test unified exports for all hosters

        (should crash on typos/missing values in unification) 
        """
        with test_app.app_context():
            mock_repos = get_mock_repos(hosting_service_type=hosting_service.type)

            repo_class = Repository.repo_class_for_type(hosting_service.type)
            repo = repo_class.from_dict(hosting_service.id, mock_repos[0])
            db.session.add(repo)
            db.session.commit()

            repo_class.rotate(hosting_service)
            repo_class.export_unified_csv_gz(hosting_service, "test_export")

    @pytest.mark.parametrize(
        "hosting_service",  # matched against hosting_service fixture in conftest.py
        [HOST_TYPE_GITEA, HOST_TYPE_GITHUB, HOST_TYPE_GITLAB],
        indirect=True,
    )
    def test_rotate(self, test_app, test_client, hosting_service):
        mock_repos = get_mock_repos(hosting_service_type=hosting_service.type)
        repo_class = Repository.repo_class_for_type(hosting_service.type)

        finished_tablename = repo_class.get_finished_table_name(
            hosting_service
        )

        repo = repo_class.from_dict(hosting_service.id, mock_repos[0])
        db.session.add(repo)
        db.session.commit()
        # we added a repo
        assert repo_class.query.count() == 1

        # rotating should move repos over to finished table
        repo_class.rotate(hosting_service)
        assert repo_class.query.count() == 0
        # check on finished table
        with TableHelper._cursor() as cur:
            assert TableHelper.count_table_rows(cur, finished_tablename) == 1

        # a second run

        mock_repos = get_mock_repos(hosting_service_type=hosting_service.type)
        repo = repo_class.from_dict(hosting_service.id, mock_repos[0])
        db.session.add(repo)
        db.session.commit()

        assert repo_class.query.count() == 1
        # rotate deletes the last run, leaving only the newest repo
        repo_class.rotate(hosting_service)
        assert repo_class.query.count() == 0
        # check on finished table
        with TableHelper._cursor() as cur:
            assert TableHelper.count_table_rows(cur, finished_tablename) == 1

