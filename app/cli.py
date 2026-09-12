import click
from flask.cli import with_appcontext

from app.database import create_schema


@click.command("init-db", help="Create the database tables if needed.")
@with_appcontext
def init_db_command():
    create_schema()
    click.echo("Database ready.")


def register_cli(app):
    app.cli.add_command(init_db_command)
