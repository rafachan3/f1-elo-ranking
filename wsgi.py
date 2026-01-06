"""
WSGI entry point for production deployment.

This file is used by gunicorn to serve the application.
Usage: gunicorn wsgi:app
"""
import os

# Set production environment if not already set
if not os.environ.get('FLASK_ENV'):
    os.environ['FLASK_ENV'] = 'production'

from main import app, init_db

# Initialize database when the application starts
# This creates tables and populates data if needed
with app.app_context():
    init_db(app)

if __name__ == "__main__":
    app.run()
