#!/usr/bin/env python
"""
Development entry point for the F1 ELO Rankings application.

Usage:
    python run.py
"""
from app import create_app
from app.services import init_db

# Create the Flask application
app = create_app()

if __name__ == "__main__":
    # Initialize database
    init_db(app)
    
    # Run development server
    app.run(debug=True)
