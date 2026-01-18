"""
Flask route blueprints.
"""
from app.routes.main import main_bp
from app.routes.rankings import rankings_bp
from app.routes.drivers import drivers_bp
from app.routes.contact import contact_bp

__all__ = ['main_bp', 'rankings_bp', 'drivers_bp', 'contact_bp']
