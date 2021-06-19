import pytest
from flask import current_app
from hubgrep_indexer import db, state_manager


class TestGithub:
    def test_get_block(self, test_app, hosting_service):
        with test_app.app_context() as app:
            response = test_app.test_client().get(
                "/api/v1/hosters/1/block"
            )
            assert response.json["from_id"] == 1
            assert response.json["to_id"] == state_manager.batch_size
            response = test_app.test_client().get(
                "/api/v1/hosters/1/block"
            )
            assert response.json["from_id"] == state_manager.batch_size +1
            assert response.json["to_id"] == state_manager.batch_size * 2
