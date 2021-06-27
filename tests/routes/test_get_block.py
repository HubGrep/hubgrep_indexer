import pytest
from flask import current_app
from hubgrep_indexer import db, state_manager

from hubgrep_indexer.lib.state_manager.abstract_state_manager import AbstractStateManager


class TestGithub:
    def _test_get_loadbalanced_block(self, test_app, hosting_service):
        """
        todo: this is a pretty weak test for now, as we only have one hoster
        we should have a test over more hosters when we have a behavior defined
        """
        with test_app.app_context():
            response = test_app.test_client().get(
                "/api/v1/hosters/github/loadbalanced_block"
            )
            assert response.json["from_id"] == 1
            assert response.json["to_id"] == state_manager.batch_size
            response = test_app.test_client().get("/api/v1/hosters/github/block")
            assert response.json["from_id"] == state_manager.batch_size + 1
            assert response.json["to_id"] == state_manager.batch_size * 2
