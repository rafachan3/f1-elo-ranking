"""
Flask application factory and extensions.
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap5
from flask_mail import Mail

# Initialize extensions (without app)
db = SQLAlchemy()
mail = Mail()
bootstrap = Bootstrap5()


def create_app(config_object=None):
    """
    Application factory for creating the Flask app.
    
    Args:
        config_object: Configuration class to use. If None, uses get_config().
    
    Returns:
        Flask application instance.
    """
    # Get the root directory of the project
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    app = Flask(
        __name__,
        template_folder=os.path.join(root_dir, 'templates'),
        static_folder=os.path.join(root_dir, 'static')
    )
    
    # Load configuration
    if config_object is None:
        from config import get_config
        config_object = get_config()
    
    app.config.from_object(config_object)
    
    # Initialize extensions with app
    db.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    
    # Register blueprints
    from app.routes import main_bp, rankings_bp, drivers_bp, contact_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(rankings_bp)
    app.register_blueprint(drivers_bp)
    app.register_blueprint(contact_bp)
    
    # Register context processors
    from app.context_processors import register_context_processors
    register_context_processors(app)
    
    return app
