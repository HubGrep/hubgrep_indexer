import pytest
from flask import current_app
from unittest.mock import MagicMock

from hubgrep_indexer.models.hosting_service import HostingService
from hubgrep_indexer.lib.hosting_service_validator import HostingServiceValidator
from tests.helpers import HOSTER_TYPES


class TestHosters:
    def test_post_get_hosters(self, test_client):
        with current_app.app_context():
            assert HostingService.query.count() == 0
            payload = dict(
                type="github",
                landingpage_url="https://github.com",
                api_url="https://api.github.com/v4/",
                api_key="secret api key"
            )

            # this is the validest hoster ever.
            HostingServiceValidator.test_hoster_is_valid = MagicMock(return_value=True)
            response = test_client.post("/api/v1/hosters",
                                        json=payload,
                                        headers={"Authorization": f"Basic {current_app.config['INDEXER_API_KEY']}"})
            assert response.status == "200 OK"
            assert HostingService.query.count() == 1
            hosting_service = HostingService.query.first()
            assert hosting_service.type == "github"

    @pytest.mark.parametrize(
        'hosting_service',  # matched against hosting_service fixture in conftest.py
        HOSTER_TYPES,
        indirect=True
    )
    def test_get_hosters(self, test_client, hosting_service):
        response = test_client.get("/api/v1/hosters")
        assert response.json[0]["api_url"] == hosting_service.api_url
        assert response.json[0].get("api_key", None) is None
        assert response.json[0].get("api_keys", None) is None

    @pytest.mark.parametrize(
        'hosting_service',  # matched against hosting_service fixture in conftest.py
        HOSTER_TYPES,
        indirect=True
    )
    def test_get_hosters_authenticated(self, test_client, hosting_service):
        response = test_client.get("/api/v1/hosters",
                                   headers={"Authorization": f"Basic {current_app.config['INDEXER_API_KEY']}"})
        assert response.json[0]["api_url"] == hosting_service.api_url
        assert response.json[0].get("api_key", None) is None
        assert response.json[0].get("api_keys", None) is not None
