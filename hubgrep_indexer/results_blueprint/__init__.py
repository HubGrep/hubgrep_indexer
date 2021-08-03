import os
from flask import Blueprint
from flask import send_from_directory

results_bp = Blueprint("results", __name__, url_prefix="/results")


@results_bp.route('/<path:path>')
def serve_files(path):
    results_path = os.environ.get('HUBGREP_RESULTS_PATH')
    return send_from_directory(results_path, path)
