from hubgrep_indexer.config import Config


class TestingConfig(Config):
    TESTING = True
    REDIS_URL = 'redis://redis'