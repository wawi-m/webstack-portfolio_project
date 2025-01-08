from abc import ABC
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime
import re

class BaseScraper(ABC):
    def __init__(self):
        self.session = None
        self.min_price = 1.0
        self.max_price = 10000000.0
        self.rate_limit_delay = 1
    
    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None
    
    def clean_price(self, price_text):
        """Clean price text and convert to float"""
        try:
            # Remove currency symbol and commas
            price_match = re.search(r'[\d,]+', price_text)
            if price_match:
                price = float(price_match.group().replace(',', ''))
                if self.min_price <= price <= self.max_price:
                    return price
        except (ValueError, TypeError):
            pass
        return None
    
    async def get_product_details(self, url):
        """Get product details from URL"""
        await self.init_session()
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    price = await self.extract_price(soup) if hasattr(self, 'extract_price') else None
                    name = await self.extract_product_name(soup) if hasattr(self, 'extract_product_name') else None
                    
                    return {
                        'name': name,
                        'price': price,
                        'url': url,
                        'timestamp': datetime.utcnow()
                    }
                return None
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None
