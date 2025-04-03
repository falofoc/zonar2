# Amazon.sa Bot

## Overview

This bot automatically finds and adds top Amazon.sa products with discounts of 10% or more to the tracking system. It runs daily, scraping Amazon.sa for products with discounts of 10% or more, selecting the top 10 best deals, and adding them to the system.

## Features

- Automatically scans Amazon.sa deals pages for discounted products
- Selects products with discounts of 10% or more
- Adds up to 10 new products daily
- Runs on a scheduled basis (default: 9:00 AM daily)
- Keeps logs of all activities for monitoring
- Uses anti-bot detection techniques to reliably fetch product information
- Adds products with the prefix "العروض اليومية" to distinguish bot-added products

## Files

Two implementations are available:

### Flask Implementation (May have compatibility issues)
- `amazon_bot.py`: Main bot implementation that finds and adds products (Flask-based)
- `bot_scheduler.py`: Scheduler that runs the bot daily at the configured time (Flask-based)

### Direct Database Implementation (Recommended)
- `amazon_bot_direct.py`: Main bot implementation using direct SQLite access
- `bot_scheduler_direct.py`: Scheduler for the direct implementation

### Common Files
- `setup_bot.py`: Helper script to set up the bot as a system service
- `logs/amazon_bot.log`: Log file for bot activities
- `logs/bot_scheduler.log`: Log file for scheduler activities

## Installation

### Prerequisites

- Python 3.6 or higher
- Required packages: requests, beautifulsoup4, fake_useragent, schedule, lxml, werkzeug
- Access to the Amazon Tracker application database

### Setup Steps

1. Make sure all the required packages are installed:
   ```
   pip install -r requirements.txt
   ```

2. Run the setup script:
   ```
   python setup_bot.py
   ```

3. Follow the instructions provided by the setup script to install the service

### Manual Setup

If you prefer to set up the bot manually:

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Test the bot by running (recommended to use the direct version):
   ```
   python amazon_bot_direct.py
   ```

3. Set up a cron job or scheduler to run the bot daily:
   ```
   # Example crontab entry to run at 9:00 AM daily
   0 9 * * * cd /path/to/app && python amazon_bot_direct.py >> /path/to/app/logs/cron.log 2>&1
   ```

## How It Works

The bot performs the following actions:

1. **User Creation**: Creates a dedicated bot user in the system if it doesn't already exist
2. **Deal Finding**: Searches multiple sources on Amazon.sa for products with good discounts:
   - Official Amazon deal pages
   - Gold Box deals
   - Popular categories with deal filters
   - Sale items
3. **Discount Verification**: Analyzes product pages to confirm discounts of 10% or more
4. **Product Selection**: Randomly selects up to 10 products from the discovered deals
5. **Product Addition**: Adds the selected products to the tracking system under the bot user account

## Configuration

The bot's behavior can be configured by editing the following constants in `amazon_bot_direct.py`:

- `BOT_USERNAME`: The username for the bot in the system (default: "amazon_bot")
- `BOT_EMAIL`: The email address for the bot (default: "bot@amazontracker.sa")
- `BOT_PASSWORD`: Password for the bot user (default: from environment variable or fallback)
- `MAX_PRODUCTS_TO_ADD`: Maximum number of products to add per run (default: 10)
- `MIN_DISCOUNT_PERCENT`: Minimum discount percentage to consider (default: 10)
- `DATABASE_PATH`: Path to the SQLite database (default: 'instance/amazon_tracker.db')

## Security

- The bot creates a dedicated user in the system
- Bot password can be set via the BOT_PASSWORD environment variable for security
- The systemd service uses a randomly generated secure password if not set

## Monitoring

You can monitor the bot's activities through:

1. Log files in the `logs/` directory
2. Checking products added by the bot in the system (products with "العروض اليومية" prefix)
3. Systemd service status (if installed as a service):
   ```
   sudo systemctl status amazon_bot.service
   ```

## Troubleshooting

If the bot isn't working correctly:

1. Check the log files for errors:
   ```
   tail -f logs/amazon_bot.log
   tail -f logs/bot_scheduler.log
   ```

2. Verify the bot user exists in the database:
   ```
   sqlite3 instance/amazon_tracker.db "SELECT id, username FROM users WHERE username='amazon_bot';"
   ```

3. Test the bot manually:
   ```
   python amazon_bot_direct.py
   ```

4. Make sure the system has internet access to reach Amazon.sa

5. If the bot can't find products, try adjusting the URLs in the `find_amazon_deals` function

## License

This bot is part of the Amazon Tracker application and is subject to the same license terms. 