from flask_sqlalchemy import SQLAlchemy

# Kept in its own module so models and the factory never import each other.
db = SQLAlchemy()
