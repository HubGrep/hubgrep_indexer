import os
from hubgrep_indexer.config import Config


class DotEnvConfig(Config):
    TESTING = True
    REDIS_URL = os.environ.get("HUBGREP_REDIS_URL", None)
    SQLALCHEMY_DATABASE_URI = os.environ.get("HUBGREP_SQLALCHEMY_DATABASE_URI", False)
    SECRET_KEY = os.environ.get("HUBGREP_SECRET_KEY", False)

    RESULTS_BASE_URL = os.environ['HUBGREP_RESULTS_BASE_URL']
    # where the actual results end up on disk
    # (docker internal)
    RESULTS_PATH = os.environ['HUBGREP_RESULTS_PATH']
