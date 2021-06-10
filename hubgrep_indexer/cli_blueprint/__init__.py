import click
from flask import Blueprint, render_template
from flask import current_app as app, request

cli_bp = Blueprint("cli", __name__)

from hubgrep_indexer import db

@cli_bp.cli.command()
def init_db():
    db.create_all()
    #user_datastore.create_user(email="test@me.com", password=hash_password("password"))
    db.session.commit()




