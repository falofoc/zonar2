"""
Update Product Images Script

This script downloads and saves images for all existing products that
don't have local images stored in the database.
"""

import time
import traceback
import logging
import os
import sys
from datetime import datetime
import trackers
import requests
from logging.handlers import RotatingFileHandler
from app.models import Product, Notification, User
from app import app, db

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')

logger = logging.getLogger('update_images')
logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler('logs/update_images.log', maxBytes=10240, backupCount=3)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(stream_handler)

def update_product_images():
    """Download and save images for products without local images"""
    logger.info("Starting image update process")
    
    try:
        with app.app_context():
            # Query for products that have image_url but no local_image
            products = Product.query.filter(
                Product.image_url.isnot(None),
                (Product.local_image.is_(None) | 
                 Product.image_content_type.is_(None))
            ).all()
            
            logger.info(f"Found {len(products)} products that need image updates")
            
            success_count = 0
            error_count = 0
            
            for i, product in enumerate(products):
                try:
                    logger.info(f"Processing product {i+1}/{len(products)}: {product.id} - {product.name}")
                    
                    # Try to download the image from the existing URL
                    if product.image_url:
                        try:
                            image_data, content_type = trackers.download_image(product.image_url)
                            if image_data and content_type:
                                product.local_image = image_data
                                product.image_content_type = content_type
                                product.last_image_update = datetime.utcnow()
                                logger.info(f"Downloaded image for product {product.id} - {len(image_data)} bytes")
                                success_count += 1
                            else:
                                logger.warning(f"Failed to download image for product {product.id}")
                                error_count += 1
                        except Exception as e:
                            logger.error(f"Error downloading image for product {product.id}: {str(e)}")
                            error_count += 1
                            
                            # If original URL fails, try fetching fresh product data
                            try:
                                logger.info(f"Trying to fetch fresh product data for {product.id}")
                                product_data = trackers.fetch_product_data(product.url)
                                
                                if product_data and product_data.get('image_binary'):
                                    product.local_image = product_data.get('image_binary')
                                    product.image_content_type = product_data.get('image_content_type')
                                    product.last_image_update = datetime.utcnow()
                                    
                                    # Update image URL if different
                                    if product_data.get('image_url') and product_data.get('image_url') != product.image_url:
                                        product.image_url = product_data.get('image_url')
                                    
                                    logger.info(f"Successfully retrieved image from fresh product data for {product.id}")
                                    success_count += 1
                                    error_count -= 1  # Cancel the previous error increment
                                else:
                                    logger.warning(f"Could not retrieve image from fresh product data for {product.id}")
                            except Exception as inner_e:
                                logger.error(f"Error fetching fresh product data for {product.id}: {str(inner_e)}")
                    else:
                        # If no image_url exists, try fetching product data
                        try:
                            logger.info(f"No image URL for product {product.id}, fetching product data")
                            product_data = trackers.fetch_product_data(product.url)
                            
                            if product_data:
                                if product_data.get('image_url'):
                                    product.image_url = product_data.get('image_url')
                                
                                if product_data.get('image_binary'):
                                    product.local_image = product_data.get('image_binary')
                                    product.image_content_type = product_data.get('image_content_type')
                                    product.last_image_update = datetime.utcnow()
                                    logger.info(f"Successfully retrieved image for {product.id}")
                                    success_count += 1
                                else:
                                    logger.warning(f"Fetched product data but no image for {product.id}")
                                    error_count += 1
                            else:
                                logger.warning(f"Could not fetch product data for {product.id}")
                                error_count += 1
                        except Exception as e:
                            logger.error(f"Error fetching product data for {product.id}: {str(e)}")
                            error_count += 1
                    
                    # Commit changes for each product to avoid losing all progress on error
                    db.session.commit()
                    
                    # Sleep between requests to avoid overwhelming Amazon
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error processing product {product.id}: {str(e)}")
                    traceback.print_exc()
                    db.session.rollback()  # Rollback on error
                    error_count += 1
                    continue
            
            logger.info(f"Image update process complete:")
            logger.info(f"- Total products processed: {len(products)}")
            logger.info(f"- Successful updates: {success_count}")
            logger.info(f"- Errors: {error_count}")
            
    except Exception as e:
        logger.error(f"Error during image update process: {str(e)}")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    update_product_images() 