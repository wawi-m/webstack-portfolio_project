import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Product, PriceHistory
from sqlalchemy import desc

def list_products():
    app = create_app()
    with app.app_context():
        products = Product.query.all()
        print("\nAll Products:")
        for p in products:
            latest_price = PriceHistory.query.filter_by(product_id=p.id).order_by(desc(PriceHistory.timestamp)).first()
            print(f"ID: {p.id} | Name: {p.name} | Platform: {p.platform} | Current Price: KES {latest_price.price if latest_price else 'N/A'}")

def search_products(term):
    app = create_app()
    with app.app_context():
        products = Product.query.filter(Product.name.ilike(f"%{term}%")).all()
        print(f"\nProducts matching '{term}':")
        for p in products:
            latest_price = PriceHistory.query.filter_by(product_id=p.id).order_by(desc(PriceHistory.timestamp)).first()
            print(f"ID: {p.id} | Name: {p.name} | Current Price: KES {latest_price.price if latest_price else 'N/A'}")

def view_price_history(product_id):
    app = create_app()
    with app.app_context():
        try:
            product = Product.query.get(product_id)
            if product:
                print(f"\nPrice history for {product.name}:")
                prices = PriceHistory.query.filter_by(product_id=product_id).order_by(desc(PriceHistory.timestamp)).all()
                for price in prices:
                    print(f"Date: {price.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | Price: KES {price.price}")
            else:
                print("Product not found!")
        except ValueError:
            print("Invalid product ID!")

def get_price_stats(product_id):
    app = create_app()
    with app.app_context():
        try:
            product = Product.query.get(product_id)
            if product:
                prices = PriceHistory.query.filter_by(product_id=product_id).all()
                if prices:
                    price_values = [p.price for p in prices]
                    print(f"\nPrice statistics for {product.name}:")
                    print(f"Minimum Price: KES {min(price_values)}")
                    print(f"Maximum Price: KES {max(price_values)}")
                    print(f"Average Price: KES {sum(price_values) / len(price_values):.2f}")
                else:
                    print("No price history found!")
            else:
                print("Product not found!")
        except ValueError:
            print("Invalid product ID!")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("List all products: python query_db.py list")
        print("Search products: python query_db.py search <term>")
        print("View price history: python query_db.py history <product_id>")
        print("Get price statistics: python query_db.py stats <product_id>")
        sys.exit(1)

    command = sys.argv[1]
    if command == "list":
        list_products()
    elif command == "search" and len(sys.argv) > 2:
        search_products(sys.argv[2])
    elif command == "history" and len(sys.argv) > 2:
        view_price_history(sys.argv[2])
    elif command == "stats" and len(sys.argv) > 2:
        get_price_stats(sys.argv[2])
    else:
        print("Invalid command or missing arguments!")
        sys.exit(1)
