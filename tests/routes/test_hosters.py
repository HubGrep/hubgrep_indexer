from hubgrep_indexer.models.hosting_service import HostingService
from hubgrep_indexer import db
from flask import current_app


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
            response = test_client.post("/api/v1/hosters", json=payload)
            assert HostingService.query.count() == 1
            hosting_service = HostingService.query.first()
            assert hosting_service.type == "github"

    def test_get_hosters(self, test_client):
        api_url = "https://api_url"
        landingpage_url = "https://landingpage_url"
        api_key = "secret api key"

        hosting_service = HostingService()

        hosting_service.api_key = api_key
        hosting_service.api_url = api_url
        hosting_service.landingpage_url = landingpage_url
        hosting_service.type = "github"
        db.session.add(hosting_service)
        db.session.commit()

        response = test_client.get("/api/v1/hosters")
        assert response.json[0]['api_url'] == api_url
        assert response.json[0]['request_headers']['access_token'] == api_key

