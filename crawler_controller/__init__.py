import logging
import os
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from crawler_controller.lib.init_logging import init_logging
from flask_security import Security, SQLAlchemyUserDatastore, auth_required, hash_password

db = SQLAlchemy()

migrate = Migrate()
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)

    app_env = os.environ.get('APP_ENV', 'development')
    config_mapping = {
        'development': 'crawler_controller.lib.config.DevelopmentConfig',
        'production': 'crawler_controller.lib.config.ProductionConfig',
        'testing': 'crawler_controller.lib.config.testingConfig',
    }

    app.config.from_object(config_mapping[app_env])

    init_logging(loglevel=app.config['LOGLEVEL'])

    db.init_app(app)
    migrate.init_app(app, db=db)


    from crawler_controller.models.github import GitHubPlatform, GitHubUser, GithubRepo
    from crawler_controller.models.user import Role, User, Crawler

    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore)

    #from .cli import *
    from crawler_controller.api_blueprint import api
    from crawler_controller.frontend_blueprint import frontend
    app.register_blueprint(api)
    app.register_blueprint(frontend)

    return app




