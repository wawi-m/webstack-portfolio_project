import sys
import os
import asyncio
from datetime import datetime, timezone

# Add the project root directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Product, PriceHistory
from app.scrapers.jumia import JumiaScraper
from app.scrapers.kilimall import KilimallScraper
from app.scrapers.jiji import JijiScraper

async def update_product_prices():
    """Update prices for all products in the database"""
    app = create_app()
    
    with app.app_context():
        # Get all products from database
        products = Product.query.all()
        print(f"Found {len(products)} products to update")
        
        # Initialize scrapers
        scrapers = {
            'jumia': JumiaScraper(),
            'kilimall': KilimallScraper(),
            'jiji': JijiScraper()
        }
        
        # Update prices
        updated = 0
        failed = 0
        
        for product in products:
            scraper = scrapers.get(product.platform.lower())
            if not scraper:
                print(f"No scraper found for platform: {product.platform}")
                continue
            
            try:
                print(f"Updating price for {product.name} from {product.platform}...")
                details = await scraper.get_product_details(product.url)
                
                if details and details['price']:
                    # Add new price history entry
                    price_history = PriceHistory(
                        product_id=product.id,
                        price=details['price'],
                        timestamp=datetime.now(timezone.utc)
                    )
                    db.session.add(price_history)
                    
                    # Update product's current price
                    product.current_price = details['price']
                    product.last_updated = datetime.now(timezone.utc)
                    
                    updated += 1
                    print(f"[OK] Updated price: {details['price']}")
                else:
                    failed += 1
                    print(f"[FAIL] Failed to get price")
            
            except Exception as e:
                failed += 1
                print(f"[ERROR] Error updating {product.name}: {str(e)}")
                
            # Add a small delay between requests to avoid rate limiting
            await asyncio.sleep(1)
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\nUpdate complete!")
            print(f"Successfully updated: {updated}")
            print(f"Failed updates: {failed}")
        except Exception as e:
            print(f"Error committing changes: {str(e)}")
            db.session.rollback()
        
        # Close scraper sessions
        for scraper in scrapers.values():
            await scraper.close_session()

if __name__ == '__main__':
    asyncio.run(update_product_prices())
