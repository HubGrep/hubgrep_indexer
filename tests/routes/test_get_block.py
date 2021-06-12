import pytest
from hubgrep_indexer.models.hosting_service import HostingService
from flask import current_app
from hubgrep_indexer import db, state_manager


@pytest.fixture(scope="function")
def test_app_with_hoster(test_app, request):
    with test_app.app_context():
        hosting_service = HostingService()
        hosting_service.api_url = "https://api.something.com/"
        hosting_service.landingpage_url = "https://something.com/"
        hosting_service.config = "{}"
        hosting_service.type = "github"
        db.session.add(hosting_service)
        db.session.commit()

        redis_prefix = hosting_service.id
    yield test_app
    def teardown():
        state_manager.reset(redis_prefix)
    request.addfinalizer(teardown)


class TestGithub:
    def test_get_block(self, test_app_with_hoster):
        with test_app_with_hoster.app_context() as app:
            response = test_app_with_hoster.test_client().get(
                "/api/v1/hosters/1/block"
            )
            assert response.json["from_id"] == 1
            assert response.json["to_id"] == state_manager.batch_size
            response = test_app_with_hoster.test_client().get(
                "/api/v1/hosters/1/block"
            )
            assert response.json["from_id"] == state_manager.batch_size +1
            assert response.json["to_id"] == state_manager.batch_size * 2
