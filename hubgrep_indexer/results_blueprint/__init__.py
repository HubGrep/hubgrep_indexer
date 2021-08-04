from flask import Blueprint
from flask import send_from_directory

from flask import current_app

results_bp = Blueprint("results", __name__, url_prefix="/results")


@results_bp.route('/<path:path>')
def serve_files(path):
    return send_from_directory(current_app.config['RESULTS_PATH'], path)
