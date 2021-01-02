from flask import Blueprint, render_template
from flask import current_app as app, request

api = Blueprint("api", __name__, url_prefix='/api/v1')

@api.route("/")
def index():
    # get a list of supported servers?
    return "Hello world!"


from crawler_controller.api_blueprint import github

