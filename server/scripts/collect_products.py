import sys
import os
import asyncio
from datetime import datetime, timezone
import random
import logging

# Add the project root directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Product, PriceHistory
from app.scrapers.jumia import JumiaScraper
from app.scrapers.kilimall import KilimallScraper
from app.scrapers.jiji import JijiScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('product_collection.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Platform-specific category URLs
PLATFORM_URLS = {
    'jumia': {
        'phones': 'https://www.jumia.co.ke/phones-tablets/',
        'televisions': 'https://www.jumia.co.ke/televisions/'
    },
    'kilimall': {
        'phones': 'https://www.kilimall.co.ke/c/phones-and-tablets-1389',
        'televisions': 'https://www.kilimall.co.ke/c/televisions-1390'
    },
    'jiji': {
        'phones': 'https://jiji.co.ke/mobile-phones',
        'televisions': 'https://jiji.co.ke/tv-dvd-equipment/tv'
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
        platform_stats = {}
        
        # Collect products from each platform and category
        for platform, categories in PLATFORM_URLS.items():
            scraper = scrapers[platform]
            logger.info(f"\nCollecting products from {platform.upper()}...")
            platform_stats[platform] = {'success': 0, 'failed': 0}
            
            for category, url in categories.items():
                logger.info(f"\nProcessing {platform} - {category}")
                try:
                    # Get product listings
                    products = await scraper.get_category_products(url)
                    
                    if not products:
                        logger.warning(f"No products found for {platform} - {category}")
                        continue
                    
                    logger.info(f"Found {len(products)} products in {platform} - {category}")
                    
                    # Process each product
                    for product_data in products[:50]:  
                        try:
                            # Check if product already exists
                            existing = Product.query.filter_by(
                                url=product_data['url']
                            ).first()
                            
                            if existing:
                                # Update price if changed
                                if existing.current_price != product_data['price']:
                                    price_history = PriceHistory(
                                        product=existing,
                                        price=product_data['price'],
                                        timestamp=datetime.now(timezone.utc)
                                    )
                                    existing.current_price = product_data['price']
                                    existing.last_updated = datetime.now(timezone.utc)
                                    db.session.add(price_history)
                                    logger.info(f"Updated price for: {product_data['name']}")
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
                            
                            total_added += 1
                            platform_stats[platform]['success'] += 1
                            logger.info(f"Added new product: {product_data['name']}")
                            
                            # Commit every few products to avoid large transactions
                            if total_added % 10 == 0:
                                db.session.commit()
                            
                        except Exception as e:
                            total_failed += 1
                            platform_stats[platform]['failed'] += 1
                            logger.error(f"Error processing product {product_data.get('name', 'Unknown')}: {str(e)}")
                            continue
                    
                    # Commit remaining products
                    db.session.commit()
                    
                except Exception as e:
                    logger.error(f"Error processing category {category} from {platform}: {str(e)}")
                    continue
                
                # Add delay between categories to avoid rate limiting
                await asyncio.sleep(random.uniform(1, 3))
        
        # Log final statistics
        logger.info("\n=== Collection Statistics ===")
        logger.info(f"Total products added: {total_added}")
        logger.info(f"Total failures: {total_failed}")
        for platform, stats in platform_stats.items():
            logger.info(f"{platform.upper()}: Added {stats['success']}, Failed {stats['failed']}")
        logger.info("===========================")

if __name__ == '__main__':
    asyncio.run(collect_products())
