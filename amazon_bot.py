"""
Amazon Bot - Automated Product Finder

This script automatically finds and adds top Amazon.sa products with discounts of 10% or more.
It runs daily to keep the platform updated with the best deals.
"""

import os
import sys
import json
import time
import random
import requests
import logging
import traceback
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from logging.handlers import RotatingFileHandler
from fake_useragent import UserAgent

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

# Bot user details - will be created if doesn't exist
BOT_USERNAME = 'amazon_bot'
BOT_EMAIL = 'bot@amazontracker.sa'  # Replace with your domain
BOT_PASSWORD = os.environ.get('BOT_PASSWORD', 'StrongBotPassword123!')  # Set via env var for security

# Number of products to add per run
MAX_PRODUCTS_TO_ADD = 10
MIN_DISCOUNT_PERCENT = 10  # Minimum 10% discount

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
    from app import app, db
    from app.models import User
    
    with app.app_context():
        # Check if bot user already exists
        bot_user = User.query.filter_by(username=BOT_USERNAME).first()
        
        if bot_user:
            logger.info(f"Bot user already exists with ID: {bot_user.id}")
            return bot_user
        
        # Create bot user if doesn't exist
        logger.info("Creating new bot user")
        bot_user = User(
            username=BOT_USERNAME,
            email=BOT_EMAIL,
            is_admin=False,  # Bot is not an admin
            email_verified=True,  # Bot doesn't need email verification
            language='ar'  # Using Arabic as default
        )
        bot_user.set_password(BOT_PASSWORD)
        
        try:
            db.session.add(bot_user)
            db.session.commit()
            logger.info(f"Bot user created successfully with ID: {bot_user.id}")
            return bot_user
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create bot user: {str(e)}")
            raise

def find_amazon_deals():
    """
    Find top Amazon.sa deals by scraping Amazon deals pages
    Returns a list of product URLs with good discounts
    """
    deal_pages = [
        'https://www.amazon.sa/-/en/deals-and-promotions/b/?ie=UTF8&node=15195542031',
        'https://www.amazon.sa/-/en/gp/goldbox',
        'https://www.amazon.sa/-/ar/deals-and-promotions/b/?ie=UTF8&node=15195542031',
        'https://www.amazon.sa/-/ar/gp/goldbox'
    ]
    
    product_links = []
    
    for deal_page in deal_pages:
        try:
            logger.info(f"Checking deal page: {deal_page}")
            headers = get_random_headers()
            response = requests.get(deal_page, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Look for deal cards/items with discount info
            deal_elements = soup.select('.a-carousel-card, .octopus-dlp-asin-card, .dealCard, .dealContainer')
            
            for deal in deal_elements:
                try:
                    # Try to find discount percentage
                    discount_elements = deal.select('span.a-color-secondary span.a-text-bold, .dealPriceText .savingsPercentage')
                    
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
                        link_element = deal.select_one('a.a-link-normal')
                        if link_element and 'href' in link_element.attrs:
                            href = link_element['href']
                            
                            # Make sure it's a full URL
                            if href.startswith('/'):
                                href = f"https://www.amazon.sa{href}"
                                
                            # Clean up the URL to get the basic product link
                            # Remove ref parameters
                            if '?' in href:
                                href = href.split('?')[0]
                                
                            # Only keep unique product URLs
                            if href not in product_links:
                                logger.info(f"Found product with {discount_percent}% discount: {href}")
                                product_links.append(href)
                except Exception as product_error:
                    logger.error(f"Error processing a product: {str(product_error)}")
                    continue
                    
            # Add a delay between pages to avoid being flagged
            time.sleep(random.uniform(3, 5))
            
        except Exception as e:
            logger.error(f"Error scraping deal page {deal_page}: {str(e)}")
            continue
    
    return product_links

def add_product_to_system(bot_user, product_url):
    """Add a product to the tracking system for the bot user"""
    import trackers
    from app import app, db
    from app.models import Product
    
    logger.info(f"Adding product: {product_url}")
    
    with app.app_context():
        try:
            # Check if product already exists for this user
            existing_product = Product.query.filter_by(user_id=bot_user.id, url=product_url).first()
            if existing_product:
                logger.info(f"Product already exists: {product_url}")
                return None
            
            # Fetch product data from Amazon
            product_data = trackers.fetch_product_data(product_url)
            
            if not product_data or not product_data.get('price'):
                logger.warning(f"Failed to fetch product data for {product_url}")
                return None
            
            # Create new product
            price_history = [{
                'price': product_data['price'],
                'date': datetime.utcnow().isoformat()
            }]
            
            # Add "Bot" to custom name to indicate it was added by the bot
            custom_name = f"العروض اليومية: {product_data['name']}"
            if len(custom_name) > 200:  # Truncate if too long
                custom_name = custom_name[:197] + "..."
            
            product = Product(
                url=product_url,
                name=product_data['name'],
                custom_name=custom_name,
                current_price=product_data['price'],
                target_price=None,  # Bot doesn't set target prices
                image_url=product_data.get('image_url'),
                local_image=product_data.get('image_binary'),
                image_content_type=product_data.get('image_content_type'),
                last_image_update=datetime.utcnow(),
                tracking_enabled=True,
                notify_on_any_change=True,
                user_id=bot_user.id,
                price_history=json.dumps(price_history)
            )
            
            db.session.add(product)
            db.session.commit()
            logger.info(f"Product added successfully: {product_data['name']}")
            return product
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding product {product_url}: {str(e)}")
            traceback.print_exc()
            return None

def run_amazon_bot():
    """Main function to run the Amazon bot"""
    logger.info("Starting Amazon.sa bot")
    
    try:
        # Ensure bot user exists
        bot_user = ensure_bot_user_exists()
        
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
            product = add_product_to_system(bot_user, url)
            if product:
                added_count += 1
            
            # Add delay between product additions
            time.sleep(random.uniform(2, 4))
        
        logger.info(f"Bot run complete. Added {added_count} new products")
        
    except Exception as e:
        logger.error(f"Error running Amazon bot: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    run_amazon_bot() 