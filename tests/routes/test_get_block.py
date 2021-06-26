import pytest
from flask import current_app
from hubgrep_indexer import db, state_manager

from hubgrep_indexer.lib.state_manager.abstract_state_manager import AbstractStateManager

from hubgrep_indexer.api_blueprint.hosters import _get_loadbalanced_block


class TestLoadbalancedBlock:
    def test_get_loadbalanced_block(self, test_app, hosting_service, hosting_service_2):
        # register two hosting_services, test load balancing
        with test_app.app_context() as app:
            state_manager: AbstractStateManager
            timed_out_hosting_service = hosting_service
            recent_hosting_service = hosting_service_2

            timed_out_hosting_service.set_run_created_ts(hosting_service.id, 0)
            recent_hosting_service.set_run_created_ts(hosting_service.id, time.time())

            block_dict = _get_loadbalanced_block(hosting_service.type)
            assert block_dict['crawler'] 
            assert block.from_id == 1


class TestGithub:
    def test_get_block(self, test_app, hosting_service):
        with test_app.app_context() as app:
            response = test_app.test_client().get("/api/v1/hosters/1/block")
            assert response.json["from_id"] == 1
            assert response.json["to_id"] == state_manager.batch_size
            response = test_app.test_client().get("/api/v1/hosters/1/block")
            assert response.json["from_id"] == state_manager.batch_size + 1
            assert response.json["to_id"] == state_manager.batch_size * 2

    def _test_get_loadbalanced_block(self, test_app, hosting_service):
        with test_app.app_context() as app:
            response = test_app.test_client().get(
                "/api/v1/hosters/github/loadbalanced_block"
            )
            assert response.json["from_id"] == 1
            assert response.json["to_id"] == state_manager.batch_size
            response = test_app.test_client().get("/api/v1/hosters/github/block")
            assert response.json["from_id"] == state_manager.batch_size + 1
            assert response.json["to_id"] == state_manager.batch_size * 2
