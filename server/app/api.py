from flask import Blueprint, jsonify, request, render_template
from app.models import Product, PriceHistory
from app import db
from datetime import datetime, timedelta
from sqlalchemy import desc, func
import plotly.graph_objects as go
import plotly.utils
import json
import pandas as pd

bp = Blueprint('api', __name__, template_folder='templates')

@bp.route('/', methods=['GET'])
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
            "price_visualization_data": "/api/v1/products/<id>/visualization/data",
            "categories": "/api/v1/categories",
            "platforms": "/api/v1/platforms",
            "stats": "/api/v1/stats"
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

@bp.route('/products', methods=['GET'])
def get_products():
    """Get all products with optional filtering"""
    try:
        # Get query parameters
        category = request.args.get('category')
        platform = request.args.get('platform')
        search = request.args.get('search')
        sort_by = request.args.get('sort')
        
        # Start with base query
        query = Product.query
        
        # Apply filters
        if category:
            query = query.filter(Product.category == category)
        if platform:
            query = query.filter(Product.platform == platform)
        if search:
            search_term = f"%{search}%"
            query = query.filter(Product.name.ilike(search_term))
            
        # Apply sorting
        if sort_by == 'price_low':
            query = query.order_by(Product.current_price.asc())
        elif sort_by == 'price_high':
            query = query.order_by(Product.current_price.desc())
        elif sort_by == 'latest':
            query = query.order_by(Product.last_updated.desc())
        
        # Execute query
        products = query.all()
        
        # Format response
        response = []
        for product in products:
            # Get price history
            price_history = PriceHistory.query.filter_by(product_id=product.id).order_by(PriceHistory.timestamp.desc()).limit(30).all()
            history = [{'price': h.price, 'timestamp': h.timestamp.isoformat()} for h in price_history]
            
            response.append({
                'id': product.id,
                'name': product.name,
                'url': product.url,
                'platform': product.platform,
                'category': product.category,
                'current_price': product.current_price,
                'last_updated': product.last_updated.isoformat(),
                'price_history': history
            })
        
        return jsonify({
            'success': True,
            'products': response,
            'total': len(response)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product with its price history"""
    product = Product.query.get_or_404(product_id)
    
    # Get price history for the last 30 days by default
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)
    
    # Get price history
    price_history = PriceHistory.query.filter(
        PriceHistory.product_id == product_id,
        PriceHistory.timestamp >= since
    ).order_by(PriceHistory.timestamp).all()
    
    return jsonify({
        **product.to_dict(),
        'price_history': [ph.to_dict() for ph in price_history]
    })

@bp.route('/products/search', methods=['GET'])
def search_products():
    """Search products by name or platform"""
    query = request.args.get('q', '')
    platform = request.args.get('platform', '')
    
    products = Product.query
    
    if query:
        products = products.filter(Product.name.ilike(f'%{query}%'))
    if platform:
        products = products.filter(Product.platform == platform)
    
    products = products.all()
    return jsonify([product.to_dict() for product in products])

@bp.route('/products/<int:product_id>/prices', methods=['GET'])
def get_price_history(product_id):
    """Get price history for a specific product"""
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)
    
    price_history = PriceHistory.query.filter(
        PriceHistory.product_id == product_id,
        PriceHistory.timestamp >= since
    ).order_by(PriceHistory.timestamp).all()
    
    return jsonify([ph.to_dict() for ph in price_history])

@bp.route('/products/<int:product_id>/visualization', methods=['GET'])
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
    
    # Convert to pandas DataFrame for easier manipulation
    df = pd.DataFrame([
        {'timestamp': ph.timestamp, 'price': ph.price}
        for ph in price_history
    ])
    
    # Calculate moving average
    df['MA7'] = df['price'].rolling(window=7, min_periods=1).mean()
    
    # Create plotly figure
    fig = go.Figure()
    
    # Add price line
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['price'],
        mode='lines+markers',
        name='Price',
        line=dict(color='#2196F3'),
        hovertemplate='%{y:,.2f} KES<br>%{x}<extra></extra>'
    ))
    
    # Add moving average line
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['MA7'],
        mode='lines',
        name='7-day MA',
        line=dict(color='#FF9800', dash='dash'),
        hovertemplate='%{y:,.2f} KES<br>%{x}<extra></extra>'
    ))
    
    # Calculate statistics
    current_price = df['price'].iloc[-1]
    min_price = df['price'].min()
    max_price = df['price'].max()
    avg_price = df['price'].mean()
    
    # Update layout
    fig.update_layout(
        title=f'Price History for {product.name}',
        xaxis_title='Date',
        yaxis_title='Price (KES)',
        hovermode='x unified',
        showlegend=True,
        annotations=[
            dict(
                x=1.0,
                y=1.05,
                showarrow=False,
                text=f'Current: {current_price:,.2f} KES<br>'
                     f'Min: {min_price:,.2f} KES<br>'
                     f'Max: {max_price:,.2f} KES<br>'
                     f'Avg: {avg_price:,.2f} KES',
                xref='paper',
                yref='paper',
                align='left',
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='#2196F3',
                borderwidth=1,
                borderpad=4
            )
        ]
    )
    
    # Convert to JSON
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return render_template(
        'visualization.html',
        graphJSON=graphJSON,
        product=product
    )

@bp.route('/products/<int:product_id>/visualization/data', methods=['GET'])
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
    
    # Convert to pandas DataFrame
    df = pd.DataFrame([
        {'timestamp': ph.timestamp, 'price': ph.price}
        for ph in price_history
    ])
    
    # Calculate statistics
    stats = {
        'current_price': float(df['price'].iloc[-1]),
        'min_price': float(df['price'].min()),
        'max_price': float(df['price'].max()),
        'avg_price': float(df['price'].mean()),
        'price_change': float(df['price'].iloc[-1] - df['price'].iloc[0]),
        'price_change_pct': float((df['price'].iloc[-1] / df['price'].iloc[0] - 1) * 100)
    }
    
    # Calculate moving average
    df['MA7'] = df['price'].rolling(window=7, min_periods=1).mean()
    
    # Prepare data for response
    data = {
        'product': product.to_dict(),
        'statistics': stats,
        'price_history': [
            {
                'timestamp': row['timestamp'].isoformat(),
                'price': float(row['price']),
                'ma7': float(row['MA7'])
            }
            for _, row in df.iterrows()
        ]
    }
    
    return jsonify(data)

@bp.route('/categories', methods=['GET'])
def get_categories():
    """Get available categories"""
    try:
        categories = [
            {'id': 'phones', 'name': 'Mobile Phones'},
            {'id': 'televisions', 'name': 'Televisions'}
        ]
        return jsonify({
            'success': True,
            'categories': categories
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/platforms', methods=['GET'])
def get_platforms():
    """Get available platforms"""
    try:
        platforms = [
            {'id': 'jumia', 'name': 'Jumia'},
            {'id': 'kilimall', 'name': 'Kilimall'},
            {'id': 'jiji', 'name': 'Jiji'}
        ]
        return jsonify({
            'success': True,
            'platforms': platforms
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/stats', methods=['GET'])
def get_stats():
    """Get platform and category statistics"""
    try:
        # Get counts by platform
        platform_stats = db.session.query(
            Product.platform,
            func.count(Product.id).label('count'),
            func.avg(Product.current_price).label('avg_price')
        ).group_by(Product.platform).all()
        
        # Get counts by category
        category_stats = db.session.query(
            Product.category,
            func.count(Product.id).label('count'),
            func.avg(Product.current_price).label('avg_price')
        ).group_by(Product.category).all()
        
        return jsonify({
            'success': True,
            'stats': {
                'platforms': [{
                    'name': stat.platform,
                    'count': stat.count,
                    'avg_price': float(stat.avg_price) if stat.avg_price else 0
                } for stat in platform_stats],
                'categories': [{
                    'name': stat.category,
                    'count': stat.count,
                    'avg_price': float(stat.avg_price) if stat.avg_price else 0
                } for stat in category_stats]
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
