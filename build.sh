#!/bin/bash
set -e  # Exit on error

# Print debugging information
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"

# Install Python dependencies
pip install -r requirements.txt

# Backup the database before any operations
echo "Checking for existing database and creating backup..."
python restore_db.py backup || echo "Backup failed or no existing database found."

# Restore the database if needed (in case of a fresh deployment)
echo "Attempting to restore database from previous backup..."
python restore_db.py restore || echo "Restore skipped - database may already exist or no backup found."

# Run database migrations to apply any schema changes
echo "Running database migrations..."
if [ -d "migrations" ]; then
    # Use Flask-Migrate to run migrations
    flask db upgrade
    echo "Database migrations applied successfully!"
else
    # First-time setup: initialize migrations if they don't exist
    echo "Initializing database for first time..."
    flask db init
    flask db migrate -m "Initial migration"
    flask db upgrade
    echo "Database initialized and migrations applied successfully!"
fi

# Create default bot configuration if it doesn't exist
if [ ! -f "bot_config.json" ]; then
    echo "Creating default Amazon bot configuration..."
    cat > bot_config.json << 'EOL'
{
    "enabled": true,
    "run_time": "09:00",
    "max_products": 10,
    "min_discount": 10,
    "bot_username": "amazon_bot",
    "bot_email": "bot@amazontracker.sa",
    "cleanup_old_products": false,
    "categories": ["electronics", "home", "kitchen", "fashion", "beauty", "toys", "sports"]
}
EOL
    echo "Bot configuration created successfully!"
fi

# Make sure logs directory exists
if [ ! -d "logs" ]; then
    mkdir -p logs
    echo "Created logs directory"
fi

# Create price_checker.py script for cron job if it doesn't exist
if [ ! -f "price_checker.py" ]; then
    echo "Creating price_checker.py for automated tasks..."
    cat > price_checker.py << 'EOL'
#!/usr/bin/env python
# Automatic price checker script for cron jobs
import os
import sys
import traceback
from datetime import datetime

# Add the current directory to the path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print(f"[{datetime.now()}] Starting automated price check")
    from app import app, db
    from app.models import Product, Notification, User
    import trackers
    import json
    from flask_mail import Message
    from app import mail

    # Run within the application context
    with app.app_context():
        # Get all products with tracking enabled
        products = Product.query.filter_by(tracking_enabled=True).all()
        print(f"Found {len(products)} products to check")
        
        for product in products:
            try:
                print(f"Checking price for product {product.id}: {product.name}")
                product_data = trackers.fetch_product_data(product.url)
                
                if not product_data or 'price' not in product_data:
                    print(f"Failed to fetch price for product {product.id}")
                    continue
                    
                new_price = product_data['price']
                old_price = product.current_price
                
                if new_price != old_price:
                    # Update price history
                    price_history = json.loads(product.price_history) if product.price_history else []
                    price_history.append({
                        'price': new_price,
                        'date': datetime.utcnow().isoformat()
                    })
                    product.price_history = json.dumps(price_history)
                    product.current_price = new_price
                    product.last_checked = datetime.utcnow()
                    
                    # Create notification if needed
                    if product.notify_on_any_change or (product.target_price and new_price <= product.target_price):
                        message = None
                        if new_price < old_price:
                            message = f"{product.custom_name or product.name}: Price dropped to {new_price} SAR"
                        else:
                            message = f"{product.custom_name or product.name}: Price increased to {new_price} SAR"
                            
                        if product.target_price and new_price <= product.target_price:
                            message += f" - Target price reached!"
                            
                        notification = Notification(
                            message=message,
                            user_id=product.user_id,
                            read=False
                        )
                        db.session.add(notification)
                        
                        # Send email notification
                        try:
                            user = User.query.get(product.user_id)
                            if user:
                                subject = "Price Alert - Amazon Saudi Tracker"
                                body = f"""
                                Hello {user.username},
                                
                                {message}
                                
                                Click here to view the product: {product.url}
                                
                                Thank you for using Amazon Saudi Tracker!
                                """
                                
                                msg = Message(subject=subject, recipients=[user.email], body=body)
                                mail.send(msg)
                                print(f"Email notification sent to {user.email}")
                        except Exception as e:
                            print(f"Failed to send email notification: {str(e)}")
                            traceback.print_exc()
                
                # Always update last_checked time
                product.last_checked = datetime.utcnow()
                
            except Exception as e:
                print(f"Error checking product {product.id}: {str(e)}")
                traceback.print_exc()
                continue
        
        # Commit all changes at once
        db.session.commit()
        print(f"[{datetime.now()}] Price check completed successfully")
        
except Exception as e:
    print(f"[{datetime.now()}] Error in price checker: {str(e)}")
    traceback.print_exc()
EOL
    chmod +x price_checker.py
fi

# Final backup after all operations
echo "Creating final backup after build completion..."
python restore_db.py backup || echo "Final backup failed."

echo "Build completed successfully!" 