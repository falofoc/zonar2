"""
Price Check Scheduler

This script is designed to run as a background process to 
periodically check prices of all tracked products.
"""

import time
import traceback
import logging
import os
import sys
import json
from datetime import datetime, timedelta
import trackers
import requests
from logging.handlers import RotatingFileHandler
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from flask import Flask
from app.models import Product, Notification, User
from app import app, db

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')

logger = logging.getLogger('price_scheduler')
logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler('logs/scheduler.log', maxBytes=10240, backupCount=5)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(stream_handler)

def check_prices():
    """Check prices for all tracked products"""
    logger.info("Starting scheduled price check")
    
    # Get all active products
    try:
        with app.app_context():
            products = Product.query.filter_by(tracking_enabled=True).all()
            logger.info(f"Found {len(products)} active products to check")
            
            # Products that were already checked in the last few hours
            recently_checked = 0
            
            # Track products with price changes
            price_changed_count = 0
            price_dropped_count = 0
            price_increased_count = 0
            target_reached_count = 0
            error_count = 0
            
            for product in products:
                try:
                    # Skip recently checked products (last 6 hours)
                    time_since_last_check = datetime.utcnow() - product.last_checked
                    if time_since_last_check < timedelta(hours=6):
                        recently_checked += 1
                        continue
                    
                    logger.info(f"Checking product {product.id}: {product.name}")
                    
                    # Fetch current price from Amazon
                    product_data = trackers.fetch_product_data(product.url)
                    if not product_data or not product_data.get('price'):
                        logger.warning(f"Failed to fetch data for product {product.id}")
                        continue
                    
                    # Get the current price
                    new_price = product_data.get('price')
                    old_price = product.current_price
                    price_changed = new_price != old_price
                    
                    # Record every price change in history
                    if price_changed:
                        # Add price to history
                        product.add_price_to_history(new_price)
                        price_changed_count += 1
                        
                        if new_price < old_price:
                            price_dropped_count += 1
                        else:
                            price_increased_count += 1
                    
                    # Update product data
                    product.current_price = new_price
                    product.last_checked = datetime.utcnow()
                    
                    # Update product image if available
                    if product_data.get('image_binary'):
                        product.local_image = product_data.get('image_binary')
                        product.image_content_type = product_data.get('image_content_type')
                        product.last_image_update = datetime.utcnow()
                    
                    # Create notifications for price changes if needed
                    if price_changed:
                        # Format price change message
                        price_diff = abs(new_price - old_price)
                        price_diff_percent = (price_diff / old_price) * 100 if old_price > 0 else 0
                        
                        # Determine notification type and message
                        if new_price < old_price:
                            # Price decreased
                            message = f"سعر {product.display_name} انخفض إلى {new_price:.2f} ريال (-{price_diff:.2f} ريال، -{price_diff_percent:.1f}%)"
                            notification_type = 'price_drop'
                        else:
                            # Price increased
                            message = f"سعر {product.display_name} ارتفع إلى {new_price:.2f} ريال (+{price_diff:.2f} ريال، +{price_diff_percent:.1f}%)"
                            notification_type = 'price_increase'
                        
                        # Create notification for price change if enabled
                        if product.notify_on_any_change:
                            notification = Notification(
                                user_id=product.user_id,
                                message=message,
                                notification_type=notification_type,
                                related_product_id=product.id
                            )
                            db.session.add(notification)
                        
                        # Check target price
                        if product.target_price and new_price <= product.target_price and old_price > product.target_price:
                            target_message = f"سعر {product.display_name} وصل للسعر المستهدف {product.target_price:.2f} ريال"
                            target_notification = Notification(
                                user_id=product.user_id,
                                message=target_message,
                                notification_type='target_reached',
                                related_product_id=product.id
                            )
                            db.session.add(target_notification)
                            target_reached_count += 1
                    
                    # Sleep a bit to avoid overwhelming Amazon
                    time.sleep(5)
                    
                except Exception as e:
                    logger.error(f"Error checking product {product.id}: {str(e)}")
                    traceback.print_exc()
                    error_count += 1
                    continue
            
            # Save all changes in one transaction
            db.session.commit()
            
            logger.info(f"Scheduled check complete:")
            logger.info(f"- Checked: {len(products) - recently_checked}")
            logger.info(f"- Skipped (recently checked): {recently_checked}")
            logger.info(f"- Price changes: {price_changed_count}")
            logger.info(f"- Price drops: {price_dropped_count}")
            logger.info(f"- Price increases: {price_increased_count}")
            logger.info(f"- Target prices reached: {target_reached_count}")
            logger.info(f"- Errors: {error_count}")
            
    except Exception as e:
        logger.error(f"Error during scheduled price check: {str(e)}")
        traceback.print_exc()
        return False
    
    return True

def run_scheduler():
    """Run the scheduler in an infinite loop"""
    logger.info("Starting price check scheduler")
    
    while True:
        try:
            check_prices()
            
            # Wait for 6 hours before next check
            logger.info(f"Next check scheduled for: {datetime.now() + timedelta(hours=6)}")
            time.sleep(6 * 60 * 60)  # 6 hours in seconds
            
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")
            traceback.print_exc()
            # Wait 15 minutes before retry after error
            time.sleep(15 * 60)

if __name__ == "__main__":
    run_scheduler() 