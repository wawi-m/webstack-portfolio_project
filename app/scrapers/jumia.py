from app.scrapers import BaseScraper
import re
from bs4 import BeautifulSoup
from datetime import datetime
import asyncio

class JumiaScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.min_price = 1.0  # Minimum valid price
        self.max_price = 10000000.0  # Maximum valid price
        self.rate_limit_delay = 1  # Delay between requests in seconds
    
    def clean_price(self, price_text):
        """Clean price text and convert to float"""
        try:
            # Remove currency symbol and commas
            cleaned = re.sub(r'[^\d.]', '', price_text)
            price = float(cleaned)
            # Validate price range
            if self.min_price <= price <= self.max_price:
                return price
        except (ValueError, TypeError):
            pass
        return None
    
    async def extract_price(self, html_content):
        try:
            # Main price element with bold style
            price_elem = html_content.select_one('span.-b.-ltr.-tal.-fs24')
            if price_elem:
                return self.clean_price(price_elem.text.strip())
            
            # Fallback price element
            price_elem = html_content.select_one('.prc')
            if price_elem:
                return self.clean_price(price_elem.text.strip())
            
        except Exception as e:
            print(f"Error extracting price: {str(e)}")
        return None
    
    async def extract_product_name(self, html_content):
        try:
            # Main product title element
            name_elem = html_content.select_one('h1.-fs20.-pts.-pbxs')
            if name_elem:
                name = name_elem.text.strip()
                return name if len(name) > 0 else None
            
            # Fallback title element
            name_elem = html_content.select_one('.name')
            if name_elem:
                name = name_elem.text.strip()
                return name if len(name) > 0 else None
            
        except Exception as e:
            print(f"Error extracting name: {str(e)}")
        return None
    
    def is_blocked_page(self, html_content):
        """Check if we've been blocked or hit a captcha"""
        blocked_indicators = [
            'captcha',
            'blocked',
            'too many requests',
            'access denied'
        ]
        page_text = html_content.get_text().lower()
        return any(indicator in page_text for indicator in blocked_indicators)
    
    async def get_product_details(self, url, max_retries=3):
        """Get product details with retry mechanism"""
        await self.init_session()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        for attempt in range(max_retries):
            try:
                # Add delay between attempts
                if attempt > 0:
                    await asyncio.sleep(self.rate_limit_delay * attempt)
                
                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # Check if we're blocked
                        if self.is_blocked_page(soup):
                            print(f"Blocked or captcha detected on attempt {attempt + 1}")
                            continue
                        
                        price = await self.extract_price(soup)
                        name = await self.extract_product_name(soup)
                        
                        if price and name:
                            return {
                                'name': name,
                                'price': price,
                                'url': url,
                                'timestamp': datetime.utcnow()
                            }
                    else:
                        print(f"HTTP {response.status} on attempt {attempt + 1}")
                
            except Exception as e:
                print(f"Error on attempt {attempt + 1}: {str(e)}")
            
            # Increase delay for next attempt
            await asyncio.sleep(self.rate_limit_delay)
        
        return None
