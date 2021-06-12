from hubgrep_indexer.models.hosting_service import HostingService
from flask import current_app


class TestHosters:
    def test_post_get_hosters(self, test_client):
        with current_app.app_context() as app:
            assert HostingService.query.count() == 0
            payload = dict(
                type="github",
                landingpage_url="https://github.com",
                api_url="https://api.github.com/v4/",
                config="{}",
            )
            response = test_client.post("/api/v1/hosters", json=payload)
            assert HostingService.query.count() == 1
            hosting_service = HostingService.query.first()
            assert hosting_service.type == "github"

