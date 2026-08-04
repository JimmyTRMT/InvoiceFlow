"""Development entry point.

Starts the Flask development server. A production deployment would run
the same create_app factory behind a real WSGI server instead.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host=app.config["HOST"], port=app.config["PORT"])
