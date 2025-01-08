import os

class Config:
    # PostgreSQL database configuration
    DB_USER = os.getenv('POSTGRES_USER', 'postgres')
    DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'password')
    DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    DB_PORT = os.getenv('POSTGRES_PORT', '5432').split(':')[0]  # Handle port mapping format
    DB_NAME = os.getenv('POSTGRES_DB', 'price_tracker')
    
    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Additional configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-this')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')
