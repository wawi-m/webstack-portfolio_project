from abc import ABC, abstractmethod
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime

class BaseScraper(ABC):
    def __init__(self):
        self.session = None
    
    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None
    
    @abstractmethod
    async def extract_price(self, html_content):
        """Extract price from HTML content"""
        pass
    
    @abstractmethod
    async def extract_product_name(self, html_content):
        """Extract product name from HTML content"""
        pass
    
    async def get_product_details(self, url):
        """Get product details from URL"""
        await self.init_session()
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    price = await self.extract_price(soup)
                    name = await self.extract_product_name(soup)
                    
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
