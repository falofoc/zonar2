#!/usr/bin/env python3
"""
Amazon Bot Scheduler (Direct Version)

This script schedules the Amazon bot to run daily at a specific time.
It uses a simple loop with sleep to perform the scheduling.
"""

import time
import traceback
import logging
import os
import sys
import schedule
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')

logger = logging.getLogger('bot_scheduler')
logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler('logs/bot_scheduler.log', maxBytes=10240, backupCount=5)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(stream_handler)

def run_scheduled_task():
    """Run the Amazon bot task"""
    logger.info("Starting scheduled Amazon bot run")
    try:
        import amazon_bot_direct
        amazon_bot_direct.run_amazon_bot()
        logger.info("Scheduled Amazon bot run completed")
    except Exception as e:
        logger.error(f"Error during scheduled bot run: {str(e)}")
        traceback.print_exc()

def run_scheduler():
    """Run the scheduler in an infinite loop"""
    logger.info("Starting Amazon bot scheduler")
    
    # Schedule the bot to run daily at 09:00 AM
    schedule.every().day.at("09:00").do(run_scheduled_task)
    
    # Also run immediately on startup for testing
    run_scheduled_task()
    
    while True:
        try:
            # Check if any scheduled tasks need to run
            schedule.run_pending()
            
            # Sleep for a minute before checking again
            time.sleep(60)
            
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