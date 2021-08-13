import pytest

from hubgrep_indexer.models.hosting_service import HostingService
from hubgrep_indexer import db
from hubgrep_indexer.constants import HOST_TYPE_GITEA


class TestHostingService:
    @pytest.mark.parametrize(
        "hosting_service",  # matched against hosting_service fixture in conftest.py
        [HOST_TYPE_GITEA],
        indirect=True,
    )
    def test_add_api_key(self, test_client, hosting_service):
        with test_client:
            # throw out potential existing keys
            hosting_service.api_keys = []
            # add a new key
            hosting_service.add_api_key("key")
            db.session.add(hosting_service)
            db.session.commit()

            same_hosting_service = HostingService.query.filter_by(
                api_url=hosting_service.api_url
            ).first()
            assert len(same_hosting_service.api_keys) == 1

            # and delete again..
            #
            print(hosting_service.api_keys)
            hosting_service.delete_api_key("key")
            db.session.add(hosting_service)
            db.session.commit()

            same_hosting_service = HostingService.query.filter_by(
                api_url=hosting_service.api_url
            ).first()
            assert len(same_hosting_service.api_keys) == 0
