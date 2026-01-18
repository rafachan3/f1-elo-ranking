"""
Vercel serverless function entry point.

This file serves as the entry point for Vercel's Python runtime.
It imports the Flask app from the main module and exposes it for Vercel.
"""
import os
import sys

# Add the parent directory to the path so we can import from root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set production environment
os.environ['FLASK_ENV'] = 'production'

from main import app, db

# Initialize database tables on cold start (won't populate data - use seed script for that)
with app.app_context():
    db.create_all()

# Export for Vercel
app = app
