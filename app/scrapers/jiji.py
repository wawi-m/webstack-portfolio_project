from app.scrapers import BaseScraper
import re
from bs4 import BeautifulSoup
from datetime import datetime
import asyncio
import json

class JijiScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.min_price = 1.0
        self.max_price = 10000000.0
        self.rate_limit_delay = 1
        self.categories = {
            'phones': 'phones-tablets',
            'electronics': 'electronics',
            'vehicles': 'vehicles',
            'property': 'property',
            'fashion': 'fashion',
            'jobs': 'jobs',
            'services': 'services',
            'home': 'home-furniture-garden',
            'computing': 'computers-laptops'
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def get_category_products(self, category_url):
        """Get products from a category page"""
        await self.init_session()
        products = []
        
        try:
            async with self.session.get(category_url, headers=self.headers) as response:
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Find all product cards
                    product_cards = soup.select('.b-list-advert__item-wrapper')
                    
                    for card in product_cards:
                        try:
                            # Extract product link and name
                            link_elem = card.select_one('a.b-list-advert__item-title')
                            if not link_elem:
                                continue
                            
                            product_url = link_elem.get('href', '')
                            if not product_url.startswith('http'):
                                product_url = 'https://jiji.co.ke' + product_url
                            
                            product_name = link_elem.text.strip()
                            
                            # Extract price
                            price_elem = card.select_one('.b-list-advert__item-price')
                            if not price_elem:
                                continue
                            price = self.clean_price(price_elem.text.strip())
                            if not price:
                                continue
                            
                            # Extract image URL
                            img_elem = card.select_one('.b-list-advert__item-image img')
                            image_url = img_elem.get('src') if img_elem else None
                            
                            products.append({
                                'name': product_name,
                                'url': product_url,
                                'price': price,
                                'image_url': image_url
                            })
                            
                        except Exception as e:
                            print(f"Error processing product card: {str(e)}")
                            continue
                    
                    return products
                else:
                    print(f"Failed to fetch category page: {response.status}")
                    return None
                
        except Exception as e:
            print(f"Error fetching category products: {str(e)}")
            return None
    
    def clean_price(self, price_text):
        """Clean price text and convert to float"""
        try:
            # Remove currency symbol and commas
            cleaned = re.sub(r'[^\d.]', '', price_text)
            price = float(cleaned)
            if self.min_price <= price <= self.max_price:
                return price
        except (ValueError, TypeError):
            pass
        return None
    
    async def extract_price(self, html_content):
        try:
            # Main price element
            price_elem = html_content.select_one('.qa-adp-price')
            if price_elem:
                return self.clean_price(price_elem.text.strip())
            
            # Alternative price element
            price_elem = html_content.select_one('.b-list-advert__item-price')
            if price_elem:
                return self.clean_price(price_elem.text.strip())
            
        except Exception as e:
            print(f"Error extracting price: {str(e)}")
        return None
    
    async def extract_product_name(self, html_content):
        try:
            # Main name element
            name_elem = html_content.select_one('.qa-adp-title')
            if name_elem:
                return name_elem.text.strip()
            
            # Alternative name element
            name_elem = html_content.select_one('.b-list-advert__item-title')
            if name_elem:
                return name_elem.text.strip()
            
        except Exception as e:
            print(f"Error extracting product name: {str(e)}")
        return None
