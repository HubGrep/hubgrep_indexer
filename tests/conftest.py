import redislite
import os
import tempfile
import pytest

from hubgrep_indexer.lib.init_logging import init_logging

from hubgrep_indexer import create_app, db, state_manager, RedisStateManager
from hubgrep_indexer.models.hosting_service import HostingService
from hubgrep_indexer.models.export_meta import ExportMeta
from hubgrep_indexer.models.repositories.gitea import GiteaRepository
from hubgrep_indexer.models.repositories.github import GithubRepository
from hubgrep_indexer.models.repositories.gitlab import GitlabRepository

from tests.helpers import HOSTER_TYPES

init_logging()


@pytest.fixture(scope="function")
def test_app(request):
    app = create_app()

    db_fd, file_path = tempfile.mkstemp()

    # always overwrite redis with redislite so that whatever a test triggers, redis will be replaced with a test version
    state_manager.redis = redislite.Redis()

    with app.app_context():
        db.create_all()
        # wipe all tables, in case anything was left over
        db.session.query(GiteaRepository).delete()
        db.session.query(GithubRepository).delete()
        db.session.query(GitlabRepository).delete()
        db.session.query(ExportMeta).delete()
        db.session.query(HostingService).delete()
        db.session.commit()

    yield app

    # https://docs.pytest.org/en/stable/fixture.html#fixture-scopes
    def teardown():
        # tear down db/redis after test
        os.close(db_fd)
        os.unlink(file_path)
        state_manager.redis.flushdb()  # always flush our test redis after a test

    request.addfinalizer(teardown)


@pytest.fixture(scope="function")
def test_client(test_app):
    ctx = test_app.test_request_context()
    ctx.push()
    yield test_app.test_client()
    ctx.pop()


@pytest.fixture()
def test_state_manager():
    state_manager.redis = redislite.Redis()
    yield state_manager
    state_manager.redis.flushdb()


def _add_hosting_service(api_url: str,
                         landingpage_url: str = "landingpage_url",
                         type: str = "github",
                         api_key: str = "secret"):
    hosting_service = HostingService()
    hosting_service.api_url = api_url
    hosting_service.landingpage_url = landingpage_url
    hosting_service.type = type
    hosting_service.api_keys = [api_key]

    db.session.add(hosting_service)
    db.session.commit()

    return hosting_service


@pytest.fixture(scope="function")
def hosting_service(test_app, request):
    hosting_service_type = request.param
    if hosting_service_type not in HOSTER_TYPES:
        raise ValueError(
            f'invalid hosting_service_type param: "{hosting_service_type}" - should be one of: {HOSTER_TYPES}')

    api_url = f"https://test_{hosting_service_type}.com/"
    with test_app.app_context():
        hosting_service = _add_hosting_service(api_url=api_url, landingpage_url=api_url, type=hosting_service_type)
        redis_prefix = hosting_service.id

    yield hosting_service

    def teardown():
        state_manager.reset(redis_prefix)

    request.addfinalizer(teardown)
