import redislite
import os
import tempfile
import pytest
import uuid

from hubgrep_indexer import create_app, db, state_manager
from hubgrep_indexer.models.export_meta import ExportMeta
from hubgrep_indexer.models.hosting_service import HostingService
from hubgrep_indexer.models.repositories.gitea import GiteaRepository
from hubgrep_indexer.models.repositories.github import GithubRepository
from hubgrep_indexer.models.repositories.gitlab import GitlabRepository
from hubgrep_indexer.constants import (
    HOST_TYPE_GITHUB,
    HOST_TYPE_GITLAB,
    HOST_TYPE_GITEA,
)
from tests.helpers import HOSTER_TYPES


@pytest.fixture(scope="function")
def test_app(request):
    app = create_app()

    db_fd, file_path = tempfile.mkstemp()

    with app.app_context():
        db.create_all()
        # all tables should be wiped on startup, and between tests, in case anything was left over
        db.session.query(GiteaRepository).delete()
        db.session.query(GithubRepository).delete()
        db.session.query(GitlabRepository).delete()
        db.session.query(ExportMeta).delete()
        db.session.query(HostingService).delete()
        db.session.commit()

    yield app

    # https://docs.pytest.org/en/stable/fixture.html#fixture-scopes
    def teardown():
        # tear down db after test
        os.close(db_fd)
        os.unlink(file_path)

    request.addfinalizer(teardown)


@pytest.fixture(scope="function")
def test_client(test_app):
    ctx = test_app.test_request_context()
    ctx.push()
    yield test_app.test_client()
    ctx.pop()


@pytest.fixture(scope="function")
def test_state_manager():
    # set up a fake redis, so we dont need a redis container for the tests
    state_manager.redis = redislite.Redis()
    yield state_manager


def _add_hosting_service(api_url: str,
                         landingpage_url: str = "landingpage_url",
                         type: str = "github",
                         api_key: str = "secret"):
    hosting_service = HostingService()
    hosting_service.api_url = api_url
    hosting_service.landingpage_url = landingpage_url
    hosting_service.type = type
    hosting_service.api_key = api_key

    db.session.add(hosting_service)
    db.session.commit()

    return hosting_service


@pytest.fixture(scope="function")
def hosting_service_github_1(test_app, request):
    api_url = f"https://api.{HOST_TYPE_GITHUB}1.com/"
    with test_app.app_context():
        hosting_service = _add_hosting_service(api_url=api_url, type=HOST_TYPE_GITHUB)
        redis_prefix = hosting_service.id

    yield hosting_service

    def teardown():
        state_manager.reset(redis_prefix)

    request.addfinalizer(teardown)


@pytest.fixture(scope="function")
def hosting_service_github_2(test_app, request):
    api_url = f"https://api.{HOST_TYPE_GITHUB}2.com/"
    with test_app.app_context():
        hosting_service = _add_hosting_service(api_url=api_url, type=HOST_TYPE_GITHUB)
        redis_prefix = hosting_service.id

    yield hosting_service

    def teardown():
        state_manager.reset(redis_prefix)

    request.addfinalizer(teardown)


@pytest.fixture(scope="function")
def hosting_service(test_app, request):
    hosting_service_type = request.param
    if hosting_service_type not in HOSTER_TYPES:
        raise ValueError(f'invalid hosting_service_type: "{hosting_service_type}" - should be one of: {HOSTER_TYPES}')

    api_url = f"https://api.test-{hosting_service_type}-{uuid.uuid4().hex}.com/"
    with test_app.app_context():
        hosting_service = _add_hosting_service(api_url=api_url, type=hosting_service_type)
        redis_prefix = hosting_service.id

    yield hosting_service

    def teardown():
        state_manager.reset(redis_prefix)

    request.addfinalizer(teardown)
