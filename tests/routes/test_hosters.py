from hubgrep_indexer.models.hosting_service import HostingService
from hubgrep_indexer.lib.hosting_service_validator import HostingServiceValidator
from flask import current_app
from unittest.mock import MagicMock

class TestHosters:
    def test_post_get_hosters(self, test_client):
        with current_app.app_context() as app:
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

    def test_get_hosters(self, test_client, hosting_service_github_1):
        response = test_client.get("/api/v1/hosters")
        assert response.json[0]["api_url"] == hosting_service_github_1.api_url

    def test_get_hosters_authenticated(self, test_client, hosting_service_github_1):
        response = test_client.get("/api/v1/hosters",
                                   headers={"Authorization": f"Basic {current_app.config['INDEXER_API_KEY']}"})
        assert response.json[0]["api_url"] == hosting_service_github_1.api_url
        assert "crawler_request_headers" in response.json[0]  # relies on api_key to have been added in hosting_service fixture
