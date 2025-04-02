#!/bin/bash
set -e  # Exit on error

# Print debugging information
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"

# Install Python dependencies
pip install -r requirements.txt

# Create the database if it doesn't exist
echo "Creating application database tables..."
python -c "from app import app, db; from app.models import User, Product, Notification; app.app_context().push(); db.create_all()"

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
    from app.models import Product, Notification
    import trackers
    import json

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

echo "Build completed successfully!" 