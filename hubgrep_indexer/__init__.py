import os
import time
import base64
import logging
import binascii
from werkzeug.serving import WSGIRequestHandler
from flask import Flask, request, g
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin

from hubgrep_indexer.lib.init_logging import init_logging
from hubgrep_indexer.lib.state_manager.redis_state_manager import RedisStateManager
from flask_executor import Executor

from werkzeug.middleware.proxy_fix import ProxyFix

logger = logging.getLogger(__name__)

db = SQLAlchemy()

migrate = Migrate()
state_manager = RedisStateManager()
login_manager = LoginManager()
executor = Executor()

app = Flask(__name__)
# fix keep-alive in dev server (dropped connections from client sessions)
WSGIRequestHandler.protocol_version = "HTTP/1.1"


def create_app():
    app = Flask(__name__)

    app_env = os.environ.get("APP_ENV", "dotenv")
    config_mapping = {
        "testing": "hubgrep_indexer.config.testing.TestingConfig",
        "dotenv": "hubgrep_indexer.config.dotenv.DotEnvConfig",
    }

    print(f"starting in {app_env} config")

    app.config.from_object(config_mapping[app_env])

    state_manager.init_app(app)

    init_logging(loglevel=app.config["LOGLEVEL"])

    db.init_app(app)
    migrate.init_app(app, db=db)
    executor.init_app(app)

    login_manager.init_app(app)
    user_crawlers = User(api_key=app.config["INDEXER_API_KEY"])

    #@app.before_request
    #def log_crawler_ids():
        #machine_id = request.headers.get('Hubgrep-Crawler-Machine-ID', False)
        #g.is_crawler_request = bool(machine_id)
        #if g.is_crawler_request:
            #g.hubgrep_request_start_ts = time.time()
            #logger.debug(
                #f"before crawler request - request-id: {request.headers.get('X-Request-ID')} - crawler-id: {request.headers.get('X-Correlation-ID')} - machine-id: {machine_id}")

    #@app.after_request
    #def time_crawler_request(response):
        #if g.is_crawler_request:
            #request_total_ts = time.time() - g.hubgrep_request_start_ts
            #logger.debug(
                #f" after crawler request - request-id: {request.headers.get('X-Request-ID', 'no-id')} - took {request_total_ts}s")
        #return response

    @login_manager.request_loader
    def load_user_from_request(request):
        # our single crawler user is hardcoded until we need something more from auth
        return is_user_authenticated(request, user_crawlers)

    from hubgrep_indexer.models.repositories.github import GithubRepository
    from hubgrep_indexer.models.repositories.gitea import GiteaRepository
    from hubgrep_indexer.models.repositories.gitlab import GitlabRepository

    from hubgrep_indexer.models.hosting_service import HostingService
    from hubgrep_indexer.models.export_meta import ExportMeta

    from hubgrep_indexer.api_blueprint import api
    from hubgrep_indexer.frontend_blueprint import frontend
    from hubgrep_indexer.cli_blueprint import cli_bp
    from hubgrep_indexer.results_blueprint import results_bp

    app.register_blueprint(api)
    app.register_blueprint(frontend)
    app.register_blueprint(cli_bp)
    app.register_blueprint(results_bp)

    # make app use the correct values from x-forwarded-for and x-forwarded-host headers
    # fixes generating wrong url_for domains and schemes
    # https://stackoverflow.com/questions/34802316/make-flasks-url-for-use-the-https-scheme-in-an-aws-load-balancer-without-mess#comment120003707_45333882
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_port=1)

    return app


class User(UserMixin):
    # Note: we dont care about storing users, so we use defaults
    def __init__(self, api_key: str = None, *args):
        self.api_key = api_key
        super().__init__(*args)


def is_user_authenticated(request, user):
    # first, try to login using the api_key url arg
    api_key = request.args.get("api_key")
    if api_key:
        if api_key == user.api_key:
            return user

    # next, try to login using Basic Auth
    api_key = request.headers.get("Authorization")
    if api_key:
        api_key = api_key.replace("Basic ", "", 1)
        try:
            api_key_b64_bytes = api_key.encode()
            api_key = base64.b64decode(api_key_b64_bytes).decode()
        except (TypeError, binascii.Error):
            # binascii.Error happens when we try to decode invalid base64 strings
            pass
        if api_key == user.api_key:
            return user

    # finally, return None if both methods did not login the user
    return None
