"""
import click
from .. import app


@app.cli.command()
@click.argument('first_arg')
def do_something(first_arg):
    print(first_arg)
"""
