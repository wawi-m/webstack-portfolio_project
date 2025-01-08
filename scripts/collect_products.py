import sys
import os
import asyncio
from datetime import datetime, timezone
import random

# Add the project root directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Product, PriceHistory
from app.scrapers.jumia import JumiaScraper
from app.scrapers.kilimall import KilimallScraper
from app.scrapers.jiji import JijiScraper

# Platform-specific category URLs
PLATFORM_URLS = {
    'jumia': {
        'phones': 'https://www.jumia.co.ke/phones-tablets/',
        'computing': 'https://www.jumia.co.ke/computing/',
        'electronics': 'https://www.jumia.co.ke/electronics/',
        'fashion': 'https://www.jumia.co.ke/fashion/',
        'health': 'https://www.jumia.co.ke/health-beauty/',
        'gaming': 'https://www.jumia.co.ke/gaming/',
        'supermarket': 'https://www.jumia.co.ke/supermarket/',
        'home': 'https://www.jumia.co.ke/home-office/',
        'baby': 'https://www.jumia.co.ke/baby-products/',
        'sporting': 'https://www.jumia.co.ke/sporting-goods/'
    },
    'kilimall': {
        'phones': 'https://www.kilimall.co.ke/phones-tablets/',
        'electronics': 'https://www.kilimall.co.ke/consumer-electronics/',
        'fashion': 'https://www.kilimall.co.ke/fashion/',
        'home': 'https://www.kilimall.co.ke/home-living/',
        'computing': 'https://www.kilimall.co.ke/computing/',
        'beauty': 'https://www.kilimall.co.ke/health-beauty/'
    },
    'jiji': {
        'phones': 'https://jiji.co.ke/phones-tablets',
        'electronics': 'https://jiji.co.ke/electronics',
        'fashion': 'https://jiji.co.ke/fashion',
        'home': 'https://jiji.co.ke/home-furniture-garden',
        'computing': 'https://jiji.co.ke/computers-laptops'
    }
}

async def collect_products():
    """Collect products from all platforms and categories"""
    app = create_app()
    
    with app.app_context():
        # Initialize scrapers
        scrapers = {
            'jumia': JumiaScraper(),
            'kilimall': KilimallScraper(),
            'jiji': JijiScraper()
        }
        
        total_added = 0
        total_failed = 0
        
        # Collect products from each platform and category
        for platform, categories in PLATFORM_URLS.items():
            scraper = scrapers[platform]
            print(f"\nCollecting products from {platform.upper()}...")
            
            for category, url in categories.items():
                print(f"\nCategory: {category}")
                try:
                    # Get product listings
                    products = await scraper.get_category_products(url)
                    if not products:
                        print(f"[WARN] No products found in {category}")
                        continue
                    
                    # Process each product
                    for product_data in products[:10]:  # Limit to 10 products per category initially
                        try:
                            # Check if product already exists
                            existing = Product.query.filter_by(
                                url=product_data['url']
                            ).first()
                            
                            if existing:
                                print(f"[SKIP] Product already exists: {product_data['name']}")
                                continue
                            
                            # Create new product
                            product = Product(
                                name=product_data['name'],
                                url=product_data['url'],
                                platform=platform,
                                category=category,
                                current_price=product_data['price'],
                                last_updated=datetime.now(timezone.utc)
                            )
                            db.session.add(product)
                            
                            # Add initial price history
                            price_history = PriceHistory(
                                product=product,
                                price=product_data['price'],
                                timestamp=datetime.now(timezone.utc)
                            )
                            db.session.add(price_history)
                            
                            # Commit changes for each product
                            db.session.commit()
                            total_added += 1
                            print(f"[OK] Added: {product_data['name']} - {product_data['price']}")
                            
                            # Random delay between products
                            await asyncio.sleep(random.uniform(1, 3))
                            
                        except Exception as e:
                            total_failed += 1
                            print(f"[ERROR] Failed to add product: {str(e)}")
                            db.session.rollback()
                    
                except Exception as e:
                    print(f"[ERROR] Failed to process category {category}: {str(e)}")
                
                # Delay between categories
                await asyncio.sleep(random.uniform(2, 5))
            
            # Close scraper session
            await scraper.close_session()
        
        print("\nCollection complete!")
        print(f"Successfully added: {total_added}")
        print(f"Failed: {total_failed}")

if __name__ == '__main__':
    asyncio.run(collect_products())
