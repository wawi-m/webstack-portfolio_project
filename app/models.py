from datetime import datetime
from app import db

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    platform = db.Column(db.String(50), nullable=False)  # e.g., 'jumia', 'kilimall', 'masoko'
    category = db.Column(db.String(50))  # Category of the product
    current_price = db.Column(db.Float)  # Current price of the product
    last_updated = db.Column(db.DateTime)  # Last time the price was updated
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    prices = db.relationship('PriceHistory', backref='product', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'platform': self.platform,
            'category': self.category,
            'current_price': self.current_price,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat()
        }

class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'price': self.price,
            'timestamp': self.timestamp.isoformat()
        }
