import os
import tempfile
import logging

import requests
import pytest

from hubgrep_indexer import create_app, db


@pytest.fixture(scope="function")
def test_app(request):
    app = create_app()
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
