import os
from dotenv import load_dotenv

load_dotenv()


def get_database_url():
    """Get database URL with proper formatting for PostgreSQL."""
    database_url = os.environ.get('DATABASE_URL', '')
    
    # Handle different PostgreSQL URL formats (Heroku uses postgres://)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    return database_url


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dev-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = os.environ.get('MAIL_PORT', 587)
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')
    MAIL_RECIPIENT = os.environ.get('MAIL_RECIPIENT')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        'sqlite:///f1-driver-elo-rankings.db'
    )


class ProductionConfig(Config):
    """Production configuration for Vercel + Neon PostgreSQL."""
    DEBUG = False
    
    # Get Neon PostgreSQL URL
    SQLALCHEMY_DATABASE_URI = get_database_url() or 'sqlite:///f1-driver-elo-rankings.db'
    
    # SQLAlchemy engine options for Neon PostgreSQL
    # Neon requires SSL and benefits from connection pooling settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Verify connections before use
        'pool_recycle': 300,    # Recycle connections after 5 minutes
    }


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on FLASK_ENV environment variable."""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
