"""Commands registered on the Flask CLI."""

import click
from flask.cli import with_appcontext

from app.database import create_schema


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Create the database tables if they do not exist yet."""
    create_schema()
    click.echo("Database ready.")


def register_cli(app):
    """Attach the project commands to the Flask CLI."""
    app.cli.add_command(init_db_command)
