import pytest

from tests.helpers import HOSTER_TYPES


class TestGetBlock:

    @pytest.mark.parametrize(
        'hosting_service',  # matched against hosting_service fixture in conftest.py
        HOSTER_TYPES,
        indirect=True
    )
    def test_get_blocks_auth(self, test_app, test_client, hosting_service):
        test_app.config["LOGIN_DISABLED"] = False
        with test_app.app_context():
            b_response = test_app.test_client().get(f"/api/v1/hosters/{hosting_service.id}/block")
            lbb_response = test_app.test_client().get(f"/api/v1/hosters/{hosting_service.type}/loadbalanced_block")
            assert b_response.status == "401 UNAUTHORIZED"
            assert lbb_response.status == "401 UNAUTHORIZED"

    @pytest.mark.parametrize(
        'hosting_service',
        HOSTER_TYPES,
        indirect=True
    )
    def test_get_block(self, test_app, hosting_service):
        """
        todo: leaving this test very basic as renaming is likely
        get a crawler block
        """
        with test_app.app_context():
            response = test_app.test_client().get(f"/api/v1/hosters/{hosting_service.id}/block")
            block = response.json
            assert block["callback_url"]
            assert block["from_id"]
            assert block["to_id"]

    @pytest.mark.parametrize(
        'hosting_service',
        HOSTER_TYPES,
        indirect=True
    )
    def test_get_loadbalanced_block(self, test_app, test_state_manager, hosting_service):
        """
        we should have a test over more hosters when we have a behavior defined
        """
        with test_app.app_context():
            response = test_app.test_client().get(
                f"/api/v1/hosters/{hosting_service.type}/loadbalanced_block"
            )
            assert response.json["from_id"] == 1
            assert response.json["to_id"] == test_state_manager.batch_size
            response = test_app.test_client().get(f"/api/v1/hosters/{hosting_service.id}/block")
            assert response.json["from_id"] == test_state_manager.batch_size + 1
            assert response.json["to_id"] == test_state_manager.batch_size * 2
