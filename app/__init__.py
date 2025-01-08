from flask import Flask, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
import os
from config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    # Get the absolute path to the frontend directory
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontenddir'))
    
    app = Flask(__name__, static_folder=frontend_dir)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            app.logger.error(f"Error creating database tables: {str(e)}")
    
    # Serve frontend files
    @app.route('/')
    def serve_frontend():
        return send_from_directory(frontend_dir, 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        try:
            return send_from_directory(frontend_dir, path)
        except Exception as e:
            app.logger.error(f"Error serving static file: {str(e)}")
            return jsonify({"error": "File not found"}), 404
    
    # Root URL route
    @app.route('/api/v1/')
    def root():
        return jsonify({
            "message": "Welcome to the E-commerce Price Tracker API",
            "version": "1.0",
            "endpoints": {
                "api_root": "/api/v1/",
                "products": "/api/v1/products",
                "product_detail": "/api/v1/products/<id>",
                "search": "/api/v1/products/search",
                "price_history": "/api/v1/products/<id>/prices",
                "price_visualization": "/api/v1/products/<id>/visualization",
                "price_visualization_data": "/api/v1/products/<id>/visualization/data"
            },
            "documentation": {
                "description": "Track and visualize e-commerce product prices across different platforms"
            }
        })
    
    # Import and register blueprints
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    return app
