import os
from hubgrep_indexer.config import Config


class DotEnvConfig(Config):
    TESTING = True
    REDIS_URL = os.environ.get("HUBGREP_REDIS_URL", None)
    SQLALCHEMY_DATABASE_URI = os.environ.get("HUBGREP_SQLALCHEMY_DATABASE_URI", False)
    SECRET_KEY = os.environ.get("HUBGREP_SECRET_KEY", False)
