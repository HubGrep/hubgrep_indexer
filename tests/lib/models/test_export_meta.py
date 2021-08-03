import datetime

import pytest
from unittest import mock

from hubgrep_indexer.models.export_meta import ExportMeta
from hubgrep_indexer.models.repositories.abstract_repository import Repository
from hubgrep_indexer.constants import HOST_TYPE_GITEA


class TestExportMeta:
    @pytest.mark.parametrize(
        "hosting_service",  # matched against hosting_service fixture in conftest.py
        [HOST_TYPE_GITEA],
        indirect=True,
    )
    def test_get_default_filename(self, hosting_service):
        timestamp = datetime.datetime.fromtimestamp(0)
        filename = ExportMeta._get_default_export_filename(
            hosting_service, timestamp, unified=False
        )

        assert filename.startswith(f"{hosting_service.hoster_name}_raw_19700101_0000")

    @pytest.mark.parametrize(
        "hosting_service",  # matched against hosting_service fixture in conftest.py
        [HOST_TYPE_GITEA],
        indirect=True,
    )
    def test_create_export(self, hosting_service):
        repo_class: Repository = Repository.repo_class_for_type(hosting_service.type)

        # mock functions that access the db
        # should be called, we make a raw export
        repo_class.export_csv_gz = mock.MagicMock()
        # should not be called
        repo_class.export_unified_csv_gz = mock.MagicMock()
        # counts the db rows..
        hosting_service.count_repos = mock.MagicMock(return_value=1)
        export = ExportMeta.create_export(
            hosting_service, "some_table", unified=False, export_filename="export"
        )

        repo_class.export_csv_gz.assert_called()
        assert export.file_path == "export"
        assert export.repo_count == 1
        assert export.is_raw is True
