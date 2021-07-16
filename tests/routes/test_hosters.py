from hubgrep_indexer.models.hosting_service import HostingService
from flask import current_app


class TestHosters:
    def test_get_hosters_auth(self, test_app, test_client):
        test_app.config["LOGIN_DISABLED"] = False
        with test_app.app_context():
            response = test_client.post("/api/v1/hosters")
            assert response.status == "401 UNAUTHORIZED"

    def test_post_get_hosters(self, test_client):
        with current_app.app_context() as app:
            assert HostingService.query.count() == 0
            payload = dict(
                type="github",
                landingpage_url="https://github.com",
                api_url="https://api.github.com/v4/",
                api_key="secret api key"
            )
            response = test_client.post("/api/v1/hosters",
                                        json=payload,
                                        headers={"Authorization": f"Basic {current_app.config['INDEXER_API_KEY']}"})
            assert response.status == "200 OK"
            assert HostingService.query.count() == 1
            hosting_service = HostingService.query.first()
            assert hosting_service.type == "github"

    def test_get_hosters(self, test_client, hosting_service):
        response = test_client.get("/api/v1/hosters")
        assert response.json[0]["api_url"] == hosting_service.api_url

    def test_get_hosters_authenticated(self, test_client, hosting_service):
        response = test_client.get("/api/v1/hosters",
                                   headers={"Authorization": f"Basic {current_app.config['INDEXER_API_KEY']}"})
        assert response.json[0]["api_url"] == hosting_service.api_url
        assert "request_headers" in response.json[0]  # relies on api_key to have been added in hosting_service fixture
