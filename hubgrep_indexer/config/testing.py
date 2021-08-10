import os
from hubgrep_indexer.config import Config


class TestingConfig(Config):
    TESTING = True
    REDIS_URL = None
    SQLALCHEMY_DATABASE_URI = "postgresql://hubgrep:hubgrep@test_postgres:5432/hubgrep"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SERVER_NAME = 'testserver'
    RESULTS_BASE_URL = 'http://results_base/'
    # where the actual results end up on disk
    # (docker internal)
    RESULTS_PATH = '/tmp/'
    OLD_RUN_AGE = 3600

    INDEXER_API_KEY = "indexerapikey"
    LOGIN_DISABLED = True

    BLOCK_MAX_RETRIES = 3
