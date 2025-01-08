from app.scrapers import BaseScraper
import re
from bs4 import BeautifulSoup
from datetime import datetime
import asyncio
import json
import logging

class KilimallScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.min_price = 1.0
        self.max_price = 10000000.0
        self.rate_limit_delay = 2  # Increased delay between requests
        self.categories = {
            'phones': 'mobile-phones?id=873&form=category',
            'televisions': 'television?id=2070&form=category'
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document'
        }
    
    def clean_product_name(self, name):
        """Clean product name by removing unwanted characters and normalizing spaces"""
        # Remove special characters and extra whitespace
        name = re.sub(r'[^\w\s\-\']', ' ', name)
        name = re.sub(r'\s+', ' ', name)
        return name.strip()
    
    async def get_category_products(self, category_url):
        """Get products from a category page"""
        await self.init_session()
        products = []
        
        try:
            full_url = f'https://www.kilimall.co.ke/category/{category_url}' if not category_url.startswith('http') else category_url
            print(f"Fetching Kilimall category: {full_url}")
            
            async with self.session.get(full_url, headers=self.headers) as response:
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Find all product cards and extract URLs
                    product_urls = []
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '')
                        if '/listing/' in href:
                            if not href.startswith('http'):
                                href = f'https://www.kilimall.co.ke{href}'
                            product_urls.append(href)
                    
                    print(f"Found {len(product_urls)} product URLs")
                    
                    # Fetch details from each product URL
                    for product_url in product_urls:
                        try:
                            await asyncio.sleep(self.rate_limit_delay)  # Rate limiting
                            
                            async with self.session.get(product_url, headers=self.headers) as product_response:
                                if product_response.status == 200:
                                    product_html = await product_response.text()
                                    product_soup = BeautifulSoup(product_html, 'html.parser')
                                    
                                    # Extract product name
                                    name_elem = product_soup.select_one('.product-title, .title, h1')
                                    if not name_elem:
                                        continue
                                        
                                    product_name = self.clean_product_name(name_elem.text)
                                    if not product_name:
                                        continue
                                    
                                    # Extract price
                                    price_elem = product_soup.select_one('.product-price, .price, .now-price, .current-price')
                                    if not price_elem:
                                        continue
                                        
                                    price_text = price_elem.text.strip()
                                    price_match = re.search(r'[\d,]+', price_text)
                                    if not price_match:
                                        continue
                                        
                                    price = float(price_match.group().replace(',', ''))
                                    if not (self.min_price <= price <= self.max_price):
                                        continue
                                    
                                    # Filter products based on category
                                    if 'television' in category_url.lower():
                                        if not any(keyword in product_name.lower() for keyword in ['tv', 'television', 'smart tv', 'led tv', 'oled']):
                                            continue
                                    elif 'phones' in category_url.lower():
                                        if not any(keyword in product_name.lower() for keyword in ['phone', 'smartphone', 'mobile', 'iphone', 'samsung', 'tecno', 'infinix']):
                                            continue
                                    
                                    products.append({
                                        'name': product_name,
                                        'url': product_url,
                                        'price': price,
                                        'platform': 'kilimall'
                                    })
                                    print(f"Added Kilimall product: {product_name}")
                                    
                        except Exception as e:
                            print(f"Error processing product URL {product_url}: {str(e)}")
                            continue
                else:
                    print(f"Failed to fetch category. Status code: {response.status}")
                    
        except Exception as e:
            print(f"Error fetching category: {str(e)}")
        
        return products
