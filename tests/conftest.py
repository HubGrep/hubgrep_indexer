import os
import tempfile
import logging

import requests
import pytest

from hubgrep_indexer import create_app, db

print('conftest!!!')

@pytest.fixture(scope="class")
def test_app():
    app = create_app()
    db_fd, file_path = tempfile.mkstemp()
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{file_path}"

    with app.app_context():
        db.create_all()
    yield app

    os.close(db_fd)
    os.unlink(file_path)


@pytest.fixture(scope="class")
def test_client(test_app):
    yield test_app.test_client()
