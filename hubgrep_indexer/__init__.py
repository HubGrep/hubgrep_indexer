from werkzeug.serving import WSGIRequestHandler
import os
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from hubgrep_indexer.lib.init_logging import init_logging
from hubgrep_indexer.lib.state_manager.redis_state_manager import RedisStateManager

import redis
import logging

db = SQLAlchemy()

migrate = Migrate()
state_manager = RedisStateManager()
logger = logging.getLogger(__name__)

# fix keep-alive in dev server (dropped connections from client sessions)
WSGIRequestHandler.protocol_version = "HTTP/1.1"


def create_app():
    app = Flask(__name__)

    app_env = os.environ.get('APP_ENV', 'dotenv')
    config_mapping = {
        'testing': 'hubgrep_indexer.config.testing.TestingConfig',
        'dotenv': 'hubgrep_indexer.config.dotenv.DotEnvConfig',
    }

    print(f"starting in {app_env} config")

    app.config.from_object(config_mapping[app_env])

    # todo: make init_app function?
    state_manager.redis = redis.from_url(app.config['REDIS_URL'])

    init_logging(loglevel=app.config['LOGLEVEL'])

    db.init_app(app)
    migrate.init_app(app, db=db)

    from hubgrep_indexer.models.repositories.github import GithubRepository
    from hubgrep_indexer.models.repositories.gitea import GiteaRepository
    from hubgrep_indexer.models.repositories.gitlab import GitlabRepository

    from hubgrep_indexer.models.hosting_service import HostingService

    from hubgrep_indexer.api_blueprint import api
    from hubgrep_indexer.frontend_blueprint import frontend
    from hubgrep_indexer.cli_blueprint import cli_bp
    from hubgrep_indexer.results_blueprint import results_bp

    app.register_blueprint(api)
    app.register_blueprint(frontend)
    app.register_blueprint(cli_bp)
    app.register_blueprint(results_bp)
    return app
