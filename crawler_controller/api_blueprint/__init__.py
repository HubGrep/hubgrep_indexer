import click
from flask import Blueprint, render_template
from flask import current_app as app, request
from flask import jsonify

api = Blueprint("api", __name__, url_prefix='/api/v1')

from crawler_controller.models.platforms import Platform
from crawler_controller.api_blueprint import github

@api.route("/")
def index():
    ''' get a list of supported servers '''
    all_platforms = Platform.query.all()
    all_platforms = [
            dict(type=p.platform_type,
                 base_url=p.base_url,
                 state = p.get_state())
            for p in all_platforms
            ]
    return jsonify(all_platforms)

