from flask import Flask, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Configure SQLite database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///price_tracker.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Serve frontend files
    @app.route('/')
    def serve_frontend():
        return send_from_directory('../frontenddir', 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory('../frontenddir', path)
    
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
                "description": "Track and visualize e-commerce product prices across different platforms",
                "features": [
                    "Product listing and search",
                    "Price history tracking",
                    "Interactive price visualizations",
                    "Statistical analysis"
                ],
                "example_ids": [1, 2, 3, 4, 5],
                "visualization_features": [
                    "Interactive line charts",
                    "7-day moving average",
                    "Price statistics dashboard",
                    "Zoom and pan controls"
                ]
            }
        })
    
    # Register blueprints
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
