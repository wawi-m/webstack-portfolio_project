import sys
import os
import asyncio
from datetime import datetime

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Product, PriceHistory
from app.scrapers.jumia import JumiaScraper

# Current Jumia product URLs
SAMPLE_PRODUCTS = [
    {
        'url': 'https://www.jumia.co.ke/fashion-ladies-rugged-body-shaper-high-waist-black-generic-mpg1113874.html',
        'platform': 'jumia'
    },
    {
        'url': 'https://www.jumia.co.ke/yoyo-classic-kids-yo-yos-led-flashing-lights-toys-generic-mpg1113875.html',
        'platform': 'jumia'
    },
    {
        'url': 'https://www.jumia.co.ke/richripple-rechargeable-2.4g-wireless-slient-mouse-bluetooth-5.0-usb-led-ultrathin-mice-generic-mpg1113876.html',
        'platform': 'jumia'
    },
    {
        'url': 'https://www.jumia.co.ke/ntk-anti-theft-brake-pedal-steering-lock-generic-mpg1113877.html',
        'platform': 'jumia'
    },
    # Add some new products
    {
        'url': 'https://www.jumia.co.ke/samsung-galaxy-a14-6.6-4gb-ram-64gb-black-183137756.html',
        'platform': 'jumia'
    },
    {
        'url': 'https://www.jumia.co.ke/tecno-spark-10c-6.6-4gb-ram-128gb-blue-185466475.html',
        'platform': 'jumia'
    }
]

async def scrape_and_save_product(scraper, product_url, platform, retries=3):
    """Scrape product details and save to database"""
    for attempt in range(retries):
        try:
            details = await scraper.get_product_details(product_url)
            if details and details['price'] and details['name']:
                # Check if product already exists
                existing_product = Product.query.filter_by(url=product_url).first()
                
                if existing_product:
                    # Update existing product name if it has changed
                    if existing_product.name != details['name']:
                        existing_product.name = details['name']
                    product = existing_product
                else:
                    product = Product(
                        name=details['name'],
                        url=product_url,
                        platform=platform
                    )
                    db.session.add(product)
                    db.session.commit()
                
                # Add price history
                price_history = PriceHistory(
                    product_id=product.id,
                    price=details['price'],
                    timestamp=datetime.utcnow()
                )
                db.session.add(price_history)
                db.session.commit()
                
                print(f"Successfully saved product: {details['name']} (Price: KES {details['price']})")
                return True
            
            if attempt < retries - 1:
                print(f"Retrying {product_url} (attempt {attempt + 2}/{retries})")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
        except Exception as e:
            print(f"Error processing {product_url} (attempt {attempt + 1}/{retries}): {str(e)}")
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
    
    return False

async def populate_database():
    """Populate database with sample products"""
    app = create_app()
    
    with app.app_context():
        scraper = JumiaScraper()
        
        try:
            success_count = 0
            total_products = len(SAMPLE_PRODUCTS)
            
            print(f"Starting database population with {total_products} products...")
            
            for i, product in enumerate(SAMPLE_PRODUCTS, 1):
                print(f"\nProcessing product {i}/{total_products}...")
                if await scrape_and_save_product(scraper, product['url'], product['platform']):
                    success_count += 1
                # Add delay between products to avoid rate limiting
                if i < total_products:
                    await asyncio.sleep(2)
            
            print(f"\nPopulation complete!")
            print(f"Successfully added/updated: {success_count}/{total_products} products")
            
            if success_count < total_products:
                print(f"Failed to process: {total_products - success_count} products")
        
        finally:
            await scraper.close_session()

if __name__ == '__main__':
    asyncio.run(populate_database())
