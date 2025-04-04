#!/bin/bash
set -e  # Exit on error

# Print debugging information
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"

# Install Python dependencies
pip install -r requirements.txt

# Set up Supabase tables and initial data
echo "Setting up Supabase..."
python setup_supabase.py || echo "Supabase setup skipped - may already be configured"

# Create price_checker.py script for cron job if it doesn't exist
if [ ! -f "price_checker.py" ]; then
    echo "Creating price_checker.py for automated tasks..."
    cat > price_checker.py << 'EOL'
#!/usr/bin/env python
import os
import sys
import traceback
from datetime import datetime
import json
from supabase import create_client, Client

# Supabase setup
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

try:
    print(f"[{datetime.now()}] Starting automated price check")
    
    # Get all products with tracking enabled
    response = supabase.table('products').select('*').eq('tracking_enabled', True).execute()
    products = response.data
    print(f"Found {len(products)} products to check")
    
    for product in products:
        try:
            print(f"Checking price for product {product['id']}: {product['name']}")
            
            # Fetch new price (implement your price fetching logic here)
            new_price = 0  # Replace with actual price fetching
            old_price = product['current_price']
            
            if new_price != old_price:
                # Update price history
                price_history = json.loads(product['price_history']) if product['price_history'] else []
                price_history.append({
                    'price': new_price,
                    'date': datetime.utcnow().isoformat()
                })
                
                # Update product
                supabase.table('products').update({
                    'price_history': json.dumps(price_history),
                    'current_price': new_price,
                    'last_checked': datetime.utcnow().isoformat()
                }).eq('id', product['id']).execute()
                
                # Create notification if needed
                if product['notify_on_any_change'] or (product['target_price'] and new_price <= product['target_price']):
                    message = None
                    if new_price < old_price:
                        message = f"{product['custom_name'] or product['name']}: Price dropped to {new_price} SAR"
                    else:
                        message = f"{product['custom_name'] or product['name']}: Price increased to {new_price} SAR"
                        
                    if product['target_price'] and new_price <= product['target_price']:
                        message += f" - Target price reached!"
                        
                    # Add notification
                    supabase.table('notifications').insert({
                        'message': message,
                        'user_id': product['user_id'],
                        'read': False
                    }).execute()
                    
                    # Send email notification
                    try:
                        user_response = supabase.table('users').select('*').eq('id', product['user_id']).execute()
                        user = user_response.data[0] if user_response.data else None
                        
                        if user:
                            # Implement your email sending logic here
                            print(f"Would send email to {user['email']}")
                    except Exception as e:
                        print(f"Failed to send email notification: {str(e)}")
                        traceback.print_exc()
            
            # Always update last_checked time
            supabase.table('products').update({
                'last_checked': datetime.utcnow().isoformat()
            }).eq('id', product['id']).execute()
            
        except Exception as e:
            print(f"Error checking product {product['id']}: {str(e)}")
            traceback.print_exc()
            continue
    
    print(f"[{datetime.now()}] Price check completed successfully")
    
except Exception as e:
    print(f"[{datetime.now()}] Error in price checker: {str(e)}")
    traceback.print_exc()
EOL
    chmod +x price_checker.py
fi

echo "Build completed successfully!" 