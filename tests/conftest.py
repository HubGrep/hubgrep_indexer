import redislite
import os
import tempfile
import logging

import requests
import pytest

from hubgrep_indexer import create_app, db
from hubgrep_indexer.models.hosting_service import HostingService
from hubgrep_indexer import db, state_manager


@pytest.fixture(scope="function")
def test_app(request):
    app = create_app()

    # set up a fake redis, so we dont need a redis container for the tests
    state_manager.redis = redislite.Redis()

    db_fd, file_path = tempfile.mkstemp()
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{file_path}"

    with app.app_context():
        db.create_all()
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
def hosting_service(test_app, request):
    with test_app.app_context():
        hosting_service = HostingService()
        hosting_service.api_url = "https://api.something.com/"
        hosting_service.landingpage_url = "https://something.com/"
        hosting_service.type = "github"
        db.session.add(hosting_service)
        db.session.commit()

        redis_prefix = hosting_service.id
    yield hosting_service
    def teardown():
        state_manager.reset(redis_prefix)
    request.addfinalizer(teardown)


@pytest.fixture(scope="function")
def hosting_service_2(test_app, request):
    with test_app.app_context():
        hosting_service = HostingService()
        hosting_service.api_url = "https://api.something2.com/"
        hosting_service.landingpage_url = "https://something2.com/"
        hosting_service.type = "github"
        db.session.add(hosting_service)
        db.session.commit()

        redis_prefix = hosting_service.id
    yield hosting_service
    def teardown():
        state_manager.reset(redis_prefix)
    request.addfinalizer(teardown)
