#!/usr/bin/env python3
"""
Amazon Bot - Automated Product Finder (Direct Database Version)

This script automatically finds and adds top Amazon.sa products with discounts of 10% or more.
It connects directly to the database without going through Flask.
"""

import os
import sys
import json
import time
import random
import requests
import logging
import traceback
import sqlite3
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from logging.handlers import RotatingFileHandler
from fake_useragent import UserAgent
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')

logger = logging.getLogger('amazon_bot')
logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler('logs/amazon_bot.log', maxBytes=10240, backupCount=5)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(stream_handler)

# Initialize user agent generator
ua = UserAgent()

# Bot user details
BOT_USERNAME = 'amazon_bot'
BOT_EMAIL = 'bot@amazontracker.sa'
BOT_PASSWORD = os.environ.get('BOT_PASSWORD', 'StrongBotPassword123!')

# Database connection - Adjust for Render.com environment
is_render = os.environ.get('RENDER', False)
if is_render:
    # On Render.com, use the /tmp directory for the database
    DATABASE_PATH = '/tmp/amazon_tracker.db'
    logger.info(f"Running in Render.com environment, using database at {DATABASE_PATH}")
else:
    # Local environment
    DATABASE_PATH = 'instance/amazon_tracker.db'
    logger.info(f"Running in local environment, using database at {DATABASE_PATH}")

# Load bot settings from config file
BOT_CONFIG_FILE = 'bot_config.json'
DEFAULT_SETTINGS = {
    'enabled': True,
    'run_time': '09:00',
    'max_products': 10,
    'min_discount': 10,
    'bot_username': 'amazon_bot',
    'bot_email': 'bot@amazontracker.sa',
    'cleanup_old_products': False,
    'categories': ['electronics', 'home', 'kitchen', 'fashion', 'beauty', 'toys', 'sports']
}

def get_bot_settings():
    """Get bot settings from config file or return defaults"""
    if os.path.exists(BOT_CONFIG_FILE):
        try:
            with open(BOT_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading bot settings: {str(e)}")
    return DEFAULT_SETTINGS.copy()

# Get settings and configure bot
settings = get_bot_settings()
MAX_PRODUCTS_TO_ADD = settings.get('max_products', 10)
MIN_DISCOUNT_PERCENT = settings.get('min_discount', 10)
BOT_USERNAME = settings.get('bot_username', 'amazon_bot')
BOT_EMAIL = settings.get('bot_email', 'bot@amazontracker.sa')

def get_db_connection():
    """Get a connection to the SQLite database"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_random_headers():
    """Generate random headers to avoid bot detection"""
    return {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
    }

def ensure_bot_user_exists():
    """Ensure that the bot user exists in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if bot user already exists
        cursor.execute('SELECT id FROM users WHERE username = ?', (BOT_USERNAME,))
        user = cursor.fetchone()
        
        if user:
            logger.info(f"Bot user already exists with ID: {user['id']}")
            return user['id']
        
        # Create bot user if doesn't exist
        logger.info("Creating new bot user")
        password_hash = generate_password_hash(BOT_PASSWORD)
        created_at = datetime.utcnow().isoformat()
        
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, language, theme, created_at, email_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (BOT_USERNAME, BOT_EMAIL, password_hash, 'ar', 'light', created_at, True))
        
        conn.commit()
        user_id = cursor.lastrowid
        logger.info(f"Bot user created successfully with ID: {user_id}")
        return user_id
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to create bot user: {str(e)}")
        raise
    finally:
        conn.close()

def find_amazon_deals():
    """
    Find top Amazon.sa deals by scraping Amazon deals pages
    Returns a list of product URLs with good discounts
    """
    deal_pages = [
        'https://www.amazon.sa/-/en/gp/goldbox',
        'https://www.amazon.sa/-/ar/gp/goldbox',
        'https://www.amazon.sa/s?k=discount&rh=p_n_deal_type%3A26931847031',
        'https://www.amazon.sa/-/en/deals?ref_=nav_cs_gb',
        'https://www.amazon.sa/-/ar/deals?ref_=nav_cs_gb',
        'https://www.amazon.sa/gcx/-/gfhz/?categoryId=departments&scrollState=eyJpdGVtSW5kZXgiOjAsInNjcm9sbE9mZnNldCI6MH0%3D&ingress=0',
        'https://www.amazon.sa/gp/bestsellers/?ref_=nav_cs_bestsellers',
        'https://www.amazon.sa/-/en/s?k=sale&ref=nb_sb_noss_1',
        'https://www.amazon.sa/-/ar/s?k=sale&ref=nb_sb_noss_1'
    ]
    
    product_links = []
    
    # First, try to find deals on the deal pages
    for deal_page in deal_pages:
        try:
            logger.info(f"Checking deal page: {deal_page}")
            headers = get_random_headers()
            response = requests.get(deal_page, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Look for deal cards/items with discount info
            deal_elements = soup.select('.a-carousel-card, .octopus-dlp-asin-card, .dealCard, .dealContainer, .a-list-item, .s-result-item, div.sg-col-inner')
            
            for deal in deal_elements:
                try:
                    # Try to find discount percentage
                    discount_elements = deal.select('span.a-color-secondary span.a-text-bold, .dealPriceText .savingsPercentage, span.a-text-strike, .a-text-price, .a-price-savings')
                    
                    discount_percent = 0
                    for discount_el in discount_elements:
                        discount_text = discount_el.text.strip()
                        if '%' in discount_text:
                            try:
                                # Extract just the number
                                discount_percent = float(discount_text.replace('%', '').replace('-', '').replace('(', '').replace(')', '').strip())
                                break
                            except ValueError:
                                continue
                    
                    # If discount is 10% or greater
                    if discount_percent >= MIN_DISCOUNT_PERCENT:
                        # Find the product link
                        link_element = deal.select_one('a.a-link-normal, .a-size-base a, h2 a, .a-text-normal, h3 a')
                        if link_element and 'href' in link_element.attrs:
                            href = link_element['href']
                            
                            # Make sure it's a full URL
                            if href.startswith('/'):
                                href = f"https://www.amazon.sa{href}"
                                
                            # Clean up the URL to get the basic product link
                            # Extract the product ID (ASIN)
                            import re
                            asin_match = re.search(r'/dp/([A-Z0-9]{10})', href)
                            if asin_match:
                                asin = asin_match.group(1)
                                clean_url = f"https://www.amazon.sa/dp/{asin}"
                                
                                # Only keep unique product URLs
                                if clean_url not in product_links:
                                    logger.info(f"Found product with {discount_percent}% discount: {clean_url}")
                                    product_links.append(clean_url)
                except Exception as product_error:
                    logger.error(f"Error processing a product: {str(product_error)}")
                    continue
                    
            # Add a delay between pages to avoid being flagged
            time.sleep(random.uniform(3, 5))
            
        except Exception as e:
            logger.error(f"Error scraping deal page {deal_page}: {str(e)}")
            continue
    
    # If we still don't have enough products, try searching for popular categories
    if len(product_links) < MAX_PRODUCTS_TO_ADD:
        categories = ['electronics', 'home', 'kitchen', 'fashion', 'beauty', 'toys', 'sports']
        for category in categories:
            if len(product_links) >= MAX_PRODUCTS_TO_ADD * 2:  # Get double what we need so we can shuffle later
                break
                
            search_url = f"https://www.amazon.sa/s?k={category}&rh=p_n_deal_type%3A26931847031"
            try:
                logger.info(f"Searching additional category: {category}")
                headers = get_random_headers()
                response = requests.get(search_url, headers=headers, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Find all product links
                product_elements = soup.select('.s-result-item')
                
                for product in product_elements:
                    # Check if we already have enough products
                    if len(product_links) >= MAX_PRODUCTS_TO_ADD * 2:
                        break
                        
                    try:
                        # Find the link to the product
                        link_element = product.select_one('h2 a, .a-link-normal')
                        if not link_element or 'href' not in link_element.attrs:
                            continue
                            
                        href = link_element['href']
                        
                        # Make sure it's a full URL
                        if href.startswith('/'):
                            href = f"https://www.amazon.sa{href}"
                            
                        # Extract the product ID (ASIN)
                        import re
                        asin_match = re.search(r'/dp/([A-Z0-9]{10})', href)
                        if asin_match:
                            asin = asin_match.group(1)
                            clean_url = f"https://www.amazon.sa/dp/{asin}"
                            
                            # Only keep unique product URLs
                            if clean_url not in product_links:
                                # Since we don't know the discount yet, we'll check later when fetching the product data
                                logger.info(f"Found potential product in {category} category: {clean_url}")
                                product_links.append(clean_url)
                    except Exception as product_error:
                        logger.error(f"Error processing a product in category search: {str(product_error)}")
                        continue
                
                # Add a delay between searches to avoid being flagged
                time.sleep(random.uniform(3, 5))
                
            except Exception as e:
                logger.error(f"Error searching category {category}: {str(e)}")
                continue
    
    return product_links

def fetch_product_data(url):
    """Fetch product data from Amazon.sa"""
    try:
        # Import trackers module for product data fetching
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import trackers
        
        # Use the trackers module to fetch data
        return trackers.fetch_product_data(url)
    except ImportError:
        logger.error("Could not import trackers module, using fallback method")
        # Use a direct simplified method as fallback
        return fetch_product_data_direct(url)

def fetch_product_data_direct(url):
    """Fallback method to fetch product data directly"""
    try:
        headers = get_random_headers()
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Get product name
        name_element = soup.select_one('#productTitle')
        name = name_element.text.strip() if name_element else "Unknown Product"
        
        # Get price - try multiple selectors
        price_selectors = [
            '.a-price .a-offscreen',
            '#priceblock_ourprice',
            '#priceblock_dealprice',
            '.a-color-price',
            '#price_inside_buybox',
            '#corePrice_feature_div .a-price .a-offscreen'
        ]
        
        price = None
        for selector in price_selectors:
            price_element = soup.select_one(selector)
            if price_element:
                # Extract just the number from the price string
                price_str = price_element.text.strip()
                price_str = ''.join(filter(lambda x: x.isdigit() or x == '.', price_str))
                try:
                    price = float(price_str)
                    break
                except ValueError:
                    continue
        
        if not price:
            return None
        
        # Get image URL
        image_element = soup.select_one('#landingImage')
        image_url = None
        if image_element:
            if 'data-old-hires' in image_element.attrs:
                image_url = image_element['data-old-hires']
            elif 'src' in image_element.attrs:
                image_url = image_element['src']
        
        return {
            'name': name,
            'price': price,
            'image_url': image_url
        }
    except Exception as e:
        logger.error(f"Error fetching product data directly: {str(e)}")
        return None

def add_product_to_system(user_id, product_url):
    """Add a product to the tracking system for the bot user"""
    logger.info(f"Adding product: {product_url}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if product already exists for this user
        cursor.execute('SELECT id FROM product WHERE user_id = ? AND url = ?', (user_id, product_url))
        existing_product = cursor.fetchone()
        
        if existing_product:
            logger.info(f"Product already exists: {product_url}")
            conn.close()
            return None
        
        # Fetch product data from Amazon
        product_data = fetch_product_data(product_url)
        
        if not product_data or not product_data.get('price'):
            logger.warning(f"Failed to fetch product data for {product_url}")
            conn.close()
            return None
        
        # For products found in category search, check if they have a significant discount
        # We'll try to estimate this by checking for price info in the product details
        try:
            headers = get_random_headers()
            response = requests.get(product_url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find any strike-through prices or "Save X%" texts
            has_discount = False
            discount_percent = 0
            
            # Check for strike-through price
            strike_price_el = soup.select_one('.a-text-price .a-offscreen, .a-text-strike')
            if strike_price_el:
                strike_price_text = strike_price_el.text.strip()
                strike_price_text = ''.join(filter(lambda x: x.isdigit() or x == '.', strike_price_text))
                try:
                    strike_price = float(strike_price_text)
                    if strike_price > product_data['price']:
                        discount_percent = ((strike_price - product_data['price']) / strike_price) * 100
                        has_discount = discount_percent >= MIN_DISCOUNT_PERCENT
                except ValueError:
                    pass
            
            # Check for "Save X%" text
            if not has_discount:
                discount_elements = soup.select('.savingsPercentage, .a-color-price')
                for el in discount_elements:
                    text = el.text.strip()
                    if '%' in text:
                        try:
                            perc_text = ''.join(filter(lambda x: x.isdigit() or x == '.', text.split('%')[0]))
                            discount_percent = float(perc_text)
                            has_discount = discount_percent >= MIN_DISCOUNT_PERCENT
                            if has_discount:
                                break
                        except ValueError:
                            continue
            
            # Only add products with significant discount
            if not has_discount:
                logger.info(f"Product {product_url} has insufficient discount ({discount_percent:.1f}%), skipping")
                conn.close()
                return None
            
            logger.info(f"Confirmed discount of {discount_percent:.1f}% for {product_url}")
            
        except Exception as e:
            # If we fail to check discount, assume it's acceptable
            logger.warning(f"Failed to check discount for {product_url}: {str(e)}")
        
        # Prepare data for insertion
        now = datetime.utcnow().isoformat()
        price_history = json.dumps([{
            'price': product_data['price'],
            'date': now
        }])
        
        # Add "العروض اليومية" to custom name to indicate it was added by the bot
        custom_name = f"العروض اليومية: {product_data['name']}"
        if len(custom_name) > 200:  # Truncate if too long
            custom_name = custom_name[:197] + "..."
        
        # Insert the product
        cursor.execute('''
            INSERT INTO product (
                url, name, custom_name, current_price, image_url,
                price_history, tracking_enabled, notify_on_any_change,
                last_checked, user_id, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            product_url, product_data['name'], custom_name, product_data['price'],
            product_data.get('image_url'), price_history, True, True,
            now, user_id, now
        ))
        
        conn.commit()
        product_id = cursor.lastrowid
        logger.info(f"Product added successfully: {product_data['name']} with ID {product_id}")
        return product_id
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding product {product_url}: {str(e)}")
        traceback.print_exc()
        return None
    finally:
        conn.close()

def run_amazon_bot():
    """Main function to run the Amazon bot"""
    logger.info("Starting Amazon.sa bot")
    
    try:
        # Ensure bot user exists
        user_id = ensure_bot_user_exists()
        
        # Find top Amazon deals
        product_urls = find_amazon_deals()
        
        if not product_urls:
            logger.warning("No suitable products found")
            return
        
        logger.info(f"Found {len(product_urls)} potential products")
        
        # Shuffle to get random products if we have more than needed
        random.shuffle(product_urls)
        
        # Limit to max number of products
        product_urls = product_urls[:MAX_PRODUCTS_TO_ADD]
        
        # Add products to the system
        added_count = 0
        for url in product_urls:
            product_id = add_product_to_system(user_id, url)
            if product_id:
                added_count += 1
            
            # Add delay between product additions
            time.sleep(random.uniform(2, 4))
        
        logger.info(f"Bot run complete. Added {added_count} new products")
        
    except Exception as e:
        logger.error(f"Error running Amazon bot: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    run_amazon_bot() 