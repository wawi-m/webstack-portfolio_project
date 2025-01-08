from flask import Blueprint, jsonify, request, render_template
from app.models import Product, PriceHistory
from app import db
from datetime import datetime, timedelta
from sqlalchemy import desc
import plotly.graph_objects as go
import plotly.utils
import json
import pandas as pd

api_bp = Blueprint('api', __name__, template_folder='templates')

@api_bp.route('/', methods=['GET'])
def index():
    """API root endpoint"""
    return jsonify({
        "message": "Welcome to the E-commerce Price Tracker API",
        "version": "1.0",
        "endpoints": {
            "products": "/api/v1/products",
            "product_detail": "/api/v1/products/<id>",
            "search": "/api/v1/products/search",
            "price_history": "/api/v1/products/<id>/prices",
            "price_visualization": "/api/v1/products/<id>/visualization",
            "price_visualization_data": "/api/v1/products/<id>/visualization/data"
        },
        "documentation": {
            "description": "Track and visualize e-commerce product prices",
            "features": [
                "Product listing and search",
                "Price history tracking",
                "Interactive price visualizations",
                "Statistical analysis"
            ],
            "example_ids": [1, 2, 3, 4, 5]
        }
    })

@api_bp.route('/products', methods=['GET'])
def get_products():
    """Get all products with their latest prices"""
    products = Product.query.all()
    return jsonify([product.to_dict() for product in products])

@api_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product with its price history"""
    product = Product.query.get_or_404(product_id)
    
    # Get price history for the last 30 days by default
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)
    
    price_history = PriceHistory.query.filter(
        PriceHistory.product_id == product_id,
        PriceHistory.timestamp >= since
    ).order_by(desc(PriceHistory.timestamp)).all()
    
    response = product.to_dict()
    response['price_history'] = [ph.to_dict() for ph in price_history]
    return jsonify(response)

@api_bp.route('/products/search', methods=['GET'])
def search_products():
    """Search products by name or platform"""
    query = request.args.get('q', '')
    platform = request.args.get('platform', '')
    
    filters = []
    if query:
        filters.append(Product.name.ilike(f'%{query}%'))
    if platform:
        filters.append(Product.platform == platform)
    
    products = Product.query.filter(*filters).all()
    return jsonify([product.to_dict() for product in products])

@api_bp.route('/products/<int:product_id>/prices', methods=['GET'])
def get_price_history(product_id):
    """Get price history for a specific product"""
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)
    
    price_history = PriceHistory.query.filter(
        PriceHistory.product_id == product_id,
        PriceHistory.timestamp >= since
    ).order_by(desc(PriceHistory.timestamp)).all()
    
    return jsonify([ph.to_dict() for ph in price_history])

@api_bp.route('/products/<int:product_id>/visualization')
def visualize_price_history(product_id):
    """Visualize price history for a specific product"""
    product = Product.query.get_or_404(product_id)
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)
    
    # Get price history
    price_history = PriceHistory.query.filter(
        PriceHistory.product_id == product_id,
        PriceHistory.timestamp >= since
    ).order_by(PriceHistory.timestamp).all()
    
    if not price_history:
        return jsonify({"error": "No price history available"}), 404
    
    # Convert to pandas DataFrame
    df = pd.DataFrame([
        {'timestamp': ph.timestamp, 'price': ph.price}
        for ph in price_history
    ])
    
    # Calculate statistics
    current_price = price_history[-1].price
    min_price = df['price'].min()
    max_price = df['price'].max()
    avg_price = df['price'].mean()
    
    # Create the plot
    fig = go.Figure()
    
    # Add price line
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['price'],
        mode='lines+markers',
        name='Price',
        line=dict(color='#007bff', width=2),
        marker=dict(size=8)
    ))
    
    # Add moving average
    df['MA7'] = df['price'].rolling(window=7, min_periods=1).mean()
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['MA7'],
        mode='lines',
        name='7-day Moving Average',
        line=dict(color='#28a745', width=2, dash='dash')
    ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text='Price History',
            x=0.5,
            xanchor='center'
        ),
        xaxis_title='Date',
        yaxis_title='Price (KES)',
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        height=500
    )
    
    # Create the plot JSON
    plot_json = json.dumps({
        'data': fig.data,
        'layout': fig.layout
    }, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Render the template
    return render_template(
        'visualization.html',
        title=product.name,
        plot=plot_json,
        current_price=current_price,
        min_price=min_price,
        max_price=max_price,
        avg_price=avg_price,
        days=days
    )

@api_bp.route('/products/<int:product_id>/visualization/data')
def get_visualization_data(product_id):
    """Get price history data for visualization in JSON format"""
    product = Product.query.get_or_404(product_id)
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)
    
    # Get price history
    price_history = PriceHistory.query.filter(
        PriceHistory.product_id == product_id,
        PriceHistory.timestamp >= since
    ).order_by(PriceHistory.timestamp).all()
    
    if not price_history:
        return jsonify({"error": "No price history available"}), 404
    
    # Convert to list of data points
    price_data = [
        {
            'timestamp': ph.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'price': ph.price
        }
        for ph in price_history
    ]
    
    # Calculate statistics
    prices = [ph.price for ph in price_history]
    current_price = prices[-1]
    min_price = min(prices)
    max_price = max(prices)
    avg_price = sum(prices) / len(prices)
    
    return jsonify({
        'product': {
            'id': product.id,
            'name': product.name,
            'platform': product.platform,
            'url': product.url
        },
        'statistics': {
            'current_price': current_price,
            'min_price': min_price,
            'max_price': max_price,
            'avg_price': avg_price,
            'data_points': len(prices),
            'date_range': {
                'start': since.strftime('%Y-%m-%d %H:%M:%S'),
                'end': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            }
        },
        'price_history': price_data
    })
