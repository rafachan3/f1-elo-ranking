"""
WSGI entry point for production deployment.

This file is used by gunicorn to serve the application.
Usage: gunicorn wsgi:app
"""
import os

# Set production environment if not already set
if not os.environ.get('FLASK_ENV'):
    os.environ['FLASK_ENV'] = 'production'

from app import create_app
from app.services import init_db

# Create the Flask application
app = create_app()

# Initialize database when the application starts
init_db(app)

if __name__ == "__main__":
    app.run()
