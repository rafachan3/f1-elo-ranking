"""
Flask context processors for template variables.
"""
from datetime import datetime


def register_context_processors(app):
    """Register all context processors with the app."""
    
    @app.context_processor
    def inject_year():
        """Inject current year into all templates."""
        return {'current_year': datetime.now().year}
