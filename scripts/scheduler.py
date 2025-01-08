import schedule
import time
import asyncio
import sys
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add the project root directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_collection.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_data_collection():
    """Run the data collection script"""
    try:
        logger.info("Starting data collection...")
        from collect_products import collect_products
        asyncio.run(collect_products())
        logger.info("Data collection completed successfully")
    except Exception as e:
        logger.error(f"Error during data collection: {str(e)}")

def main():
    """Main function to schedule and run data collection"""
    logger.info("Starting scheduler...")
    
    # Run immediately on startup
    run_data_collection()
    
    # Schedule to run every 6 hours
    schedule.every(6).hours.do(run_data_collection)
    
    # Keep the script running
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute for pending tasks
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in scheduler: {str(e)}")
            # Wait before retrying
            time.sleep(300)

if __name__ == "__main__":
    main()
