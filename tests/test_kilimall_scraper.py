import asyncio
import sys
import logging
from app.scrapers.kilimall import KilimallScraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_kilimall_scraper():
    scraper = None
    try:
        scraper = KilimallScraper()
        
        # Test mobile phones category
        logger.info("\nTesting mobile phones category...")
        phones_url = 'https://www.kilimall.co.ke/category/mobile-phones?id=873&form=category'
        phones = await scraper.get_category_products(phones_url)
        logger.info(f"Found {len(phones)} phone products")
        for product in phones[:5]:  # Show first 5 products
            logger.info(f"Phone: {product['name']} - Price: KES {product['price']}")
        
        # Test TVs category
        logger.info("\nTesting TVs category...")
        tv_url = 'https://www.kilimall.co.ke/category/television?id=2070&form=category'
        tvs = await scraper.get_category_products(tv_url)
        logger.info(f"Found {len(tvs)} TV products")
        for product in tvs[:5]:  # Show first 5 products
            logger.info(f"TV: {product['name']} - Price: KES {product['price']}")
            
    except Exception as e:
        logger.error(f"Error testing Kilimall scraper: {str(e)}")
        raise
    finally:
        if scraper:
            await scraper.close_session()

if __name__ == "__main__":
    asyncio.run(test_kilimall_scraper())
