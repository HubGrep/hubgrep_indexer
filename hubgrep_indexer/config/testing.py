from hubgrep_indexer.config import Config


class TestingConfig(Config):
    TESTING = True
    REDIS_URL = 'redis://redis/1'
    SERVER_NAME = 'testserver'
    RESULTS_BASE_URL = 'http://results_base/'
    # where the actual results end up on disk
    # (docker internal)
    RESULTS_PATH = '/tmp/'
    OLD_RUN_AGE = 3600

    INDEXER_API_KEY = "indexerapikey"
    LOGIN_DISABLED = True