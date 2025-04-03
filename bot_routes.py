import os
import re
import json
import subprocess
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
import sqlite3

bot_bp = Blueprint('bot', __name__)

# Configuration file path
BOT_CONFIG_FILE = 'bot_config.json'
LOG_FILES = {
    'bot': 'logs/amazon_bot.log',
    'scheduler': 'logs/bot_scheduler.log'
}

# Default bot settings
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
        except:
            pass
    return DEFAULT_SETTINGS.copy()

def save_bot_settings(settings):
    """Save bot settings to config file"""
    with open(BOT_CONFIG_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def get_db_connection():
    """Get a connection to the SQLite database"""
    conn = sqlite3.connect('instance/amazon_tracker.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_bot_user_id():
    """Get the bot user ID from the database"""
    settings = get_bot_settings()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if bot user exists
        cursor.execute('SELECT id FROM users WHERE username = ?', (settings['bot_username'],))
        user = cursor.fetchone()
        
        if user:
            return user['id']
    except Exception as e:
        print(f"Error getting bot user: {str(e)}")
    finally:
        conn.close()
    
    return None

def get_bot_statistics():
    """Get statistics about the bot's activity"""
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - datetime.timedelta(days=1)
    bot_user_id = get_bot_user_id()
    
    if not bot_user_id:
        return {
            'bot_active': False,
            'products_added_today': 0,
            'total_products_added': 0,
            'last_run': 'Never',
            'next_run': 'Not scheduled',
            'success_rate': 0,
            'pages_checked': 0,
            'products_found': 0,
            'average_discount': 0,
            'last_error': None
        }
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get today's products count
        cursor.execute('''
            SELECT COUNT(*) as count FROM product 
            WHERE user_id = ? AND created_at >= ?
        ''', (bot_user_id, today.isoformat()))
        today_count = cursor.fetchone()['count']
        
        # Get total products count
        cursor.execute('SELECT COUNT(*) as count FROM product WHERE user_id = ?', (bot_user_id,))
        total_count = cursor.fetchone()['count']
        
        # Get average discount (assuming we can calculate this from price history)
        cursor.execute('''
            SELECT AVG((json_extract(json_extract(price_history, '$[0].price'), '$') - 
                       current_price) / json_extract(json_extract(price_history, '$[0].price'), '$') * 100) 
            as avg_discount 
            FROM product 
            WHERE user_id = ? AND 
                  json_extract(json_extract(price_history, '$[0].price'), '$') > current_price
        ''', (bot_user_id,))
        avg_result = cursor.fetchone()
        average_discount = avg_result['avg_discount'] if avg_result and avg_result['avg_discount'] else 0
        
        # Get last run time from logs
        last_run = 'Never'
        next_run = 'Not scheduled'
        pages_checked = 0
        products_found = 0
        last_error = None
        success_rate = 0
        
        if os.path.exists(LOG_FILES['bot']):
            with open(LOG_FILES['bot'], 'r') as f:
                log_content = f.read()
                
                # Find last run time
                last_run_match = re.findall(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) INFO: Starting Amazon.sa bot', log_content)
                if last_run_match:
                    last_run = last_run_match[-1]
                
                # Get pages checked count
                pages_checked = len(re.findall(r'INFO: Checking deal page:', log_content))
                
                # Get products found count
                products_found = len(re.findall(r'INFO: Found product with', log_content)) + len(re.findall(r'INFO: Found potential product in', log_content))
                
                # Get last error
                error_matches = re.findall(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} ERROR: (.+?)(?=\n\d{4}-\d{2}-\d{2}|\Z)', log_content, re.DOTALL)
                if error_matches:
                    last_error = error_matches[-1].strip().split('\n')[0]
        
        # Get next scheduled run from scheduler settings
        settings = get_bot_settings()
        if settings['enabled']:
            try:
                today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                run_time_parts = settings['run_time'].split(':')
                next_run_time = today.replace(hour=int(run_time_parts[0]), minute=int(run_time_parts[1]))
                
                if next_run_time < datetime.datetime.now():
                    next_run_time = next_run_time + datetime.timedelta(days=1)
                
                next_run = next_run_time.strftime('%Y-%m-%d %H:%M')
            except:
                next_run = f"Today at {settings['run_time']}"
        
        # Calculate success rate
        if products_found > 0:
            success_rate = min(100, round((total_count / products_found) * 100))
        
        return {
            'bot_active': settings['enabled'],
            'products_added_today': today_count,
            'total_products_added': total_count,
            'last_run': last_run,
            'next_run': next_run,
            'success_rate': success_rate,
            'pages_checked': pages_checked,
            'products_found': products_found,
            'average_discount': round(average_discount, 1) if average_discount else 0,
            'last_error': last_error
        }
    
    except Exception as e:
        print(f"Error getting bot statistics: {str(e)}")
        return {
            'bot_active': False,
            'products_added_today': 0,
            'total_products_added': 0,
            'last_run': 'Error',
            'next_run': 'Error',
            'success_rate': 0,
            'pages_checked': 0,
            'products_found': 0,
            'average_discount': 0,
            'last_error': str(e)
        }
    finally:
        conn.close()

def get_recent_products(limit=10):
    """Get recently added products by the bot"""
    bot_user_id = get_bot_user_id()
    if not bot_user_id:
        return []
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, name, custom_name, url, current_price, image_url, created_at
            FROM product
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (bot_user_id, limit))
        
        products = []
        for row in cursor.fetchall():
            product = dict(row)
            
            # Try to extract discount from custom name or calculate if possible
            discount = 0
            if product['custom_name'] and ':' in product['custom_name']:
                # Try to parse discount from name if it contains percentage
                match = re.search(r'(\d+)%', product['custom_name'])
                if match:
                    discount = int(match.group(1))
            
            # Format date
            if 'created_at' in product and product['created_at']:
                try:
                    dt = datetime.datetime.fromisoformat(product['created_at'])
                    product['created_at'] = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            product['discount'] = discount
            products.append(product)
        
        return products
    
    except Exception as e:
        print(f"Error getting recent products: {str(e)}")
        return []
    finally:
        conn.close()

def parse_log_file(log_file, page=1, level='all', lines_per_page=100):
    """Parse log file and return entries with pagination"""
    if not os.path.exists(log_file):
        return [], 0, 0, 0, 0, 1
    
    with open(log_file, 'r') as f:
        log_lines = f.readlines()
    
    entries = []
    info_count = 0
    warning_count = 0
    error_count = 0
    
    for line in log_lines:
        # Parse log entry using regex to extract timestamp, level, and message
        match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) (\w+): (.+)', line)
        if match:
            timestamp, log_level, message = match.groups()
            
            # Count by level
            if log_level == 'INFO':
                info_count += 1
            elif log_level == 'WARNING':
                warning_count += 1
            elif log_level == 'ERROR':
                error_count += 1
            
            # Filter by level if specified
            if level != 'all' and level.upper() != log_level.upper():
                continue
            
            entries.append({
                'timestamp': timestamp,
                'level': log_level,
                'message': message
            })
    
    # Calculate pagination
    total_entries = len(entries)
    total_pages = max(1, (total_entries + lines_per_page - 1) // lines_per_page)
    page = max(1, min(page, total_pages))
    
    # Get entries for the current page
    start_idx = (page - 1) * lines_per_page
    end_idx = start_idx + lines_per_page
    page_entries = entries[start_idx:end_idx]
    
    return page_entries, info_count, warning_count, error_count, total_entries, total_pages

@bot_bp.route('/bot')
@login_required
def bot_interface():
    """Show the bot interface dashboard"""
    if not current_user.is_admin:
        flash('You must be an administrator to access this page.', 'danger')
        return redirect(url_for('home'))
    
    stats = get_bot_statistics()
    recent_products = get_recent_products(10)
    
    return render_template('bot_interface.html', **stats, recent_products=recent_products)

@bot_bp.route('/bot/settings', methods=['GET', 'POST'])
@login_required
def bot_settings():
    """Show and handle bot settings"""
    if not current_user.is_admin:
        flash('You must be an administrator to access this page.', 'danger')
        return redirect(url_for('home'))
    
    # Handle form submission
    if request.method == 'POST':
        settings = get_bot_settings()
        
        # Update settings from form
        settings['enabled'] = 'enabled' in request.form
        settings['run_time'] = request.form.get('run_time', DEFAULT_SETTINGS['run_time'])
        settings['max_products'] = int(request.form.get('max_products', DEFAULT_SETTINGS['max_products']))
        settings['min_discount'] = int(request.form.get('min_discount', DEFAULT_SETTINGS['min_discount']))
        settings['bot_username'] = request.form.get('bot_username', DEFAULT_SETTINGS['bot_username'])
        settings['bot_email'] = request.form.get('bot_email', DEFAULT_SETTINGS['bot_email'])
        settings['cleanup_old_products'] = 'cleanup_old_products' in request.form
        
        # Handle bot password if provided
        bot_password = request.form.get('bot_password')
        if bot_password and bot_password.strip():
            # Update password in database
            bot_user_id = get_bot_user_id()
            if bot_user_id:
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    password_hash = generate_password_hash(bot_password)
                    cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', 
                                  (password_hash, bot_user_id))
                    conn.commit()
                except Exception as e:
                    print(f"Error updating bot password: {str(e)}")
                finally:
                    conn.close()
        
        # Get selected categories
        settings['categories'] = request.form.getlist('categories')
        
        # Save settings
        save_bot_settings(settings)
        flash('Bot settings saved successfully.', 'success')
        return redirect(url_for('bot.bot_settings'))
    
    # Display settings form
    settings = get_bot_settings()
    
    # Get categories from database or use default list
    categories = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT category FROM product')
        for row in cursor.fetchall():
            if row['category']:
                categories.append({'id': row['category'], 'name': row['category'].capitalize()})
    except:
        # Use default categories if db query fails
        for cat in DEFAULT_SETTINGS['categories']:
            categories.append({'id': cat, 'name': cat.capitalize()})
    finally:
        conn.close()
    
    return render_template('bot_settings.html', settings=settings, categories=categories)

@bot_bp.route('/bot/logs')
@login_required
def view_bot_logs():
    """View bot logs"""
    if not current_user.is_admin:
        flash('You must be an administrator to access this page.', 'danger')
        return redirect(url_for('home'))
    
    # Get parameters
    log_type = request.args.get('log_type', 'bot')
    page = int(request.args.get('page', 1))
    level = request.args.get('level', 'all')
    
    # Make sure log_type is valid
    if log_type not in LOG_FILES:
        log_type = 'bot'
    
    # Parse logs
    log_entries, info_count, warning_count, error_count, total_entries, total_pages = parse_log_file(
        LOG_FILES[log_type], page, level
    )
    
    return render_template('bot_logs.html', 
                          log_entries=log_entries,
                          log_type=log_type,
                          page=page,
                          level=level,
                          info_count=info_count,
                          warning_count=warning_count,
                          error_count=error_count,
                          total_pages=total_pages)

@bot_bp.route('/bot/run', methods=['GET', 'POST'])
@login_required
def run_bot():
    """Run the bot manually"""
    if not current_user.is_admin:
        flash('You must be an administrator to access this page.', 'danger')
        return redirect(url_for('home'))
    
    try:
        # Run the bot in the background
        subprocess.Popen(['python', 'amazon_bot_direct.py'], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE)
        flash('Bot has been started. Check logs for results.', 'success')
    except Exception as e:
        flash(f'Error starting bot: {str(e)}', 'danger')
    
    return redirect(url_for('bot.bot_interface'))

@bot_bp.route('/bot/download-logs')
@login_required
def download_logs():
    """Download bot logs as a zip file"""
    if not current_user.is_admin:
        flash('You must be an administrator to access this page.', 'danger')
        return redirect(url_for('home'))
    
    import zipfile
    from io import BytesIO
    
    # Create a ZIP file in memory
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for log_name, log_path in LOG_FILES.items():
            if os.path.exists(log_path):
                zf.write(log_path, os.path.basename(log_path))
    
    memory_file.seek(0)
    return send_file(
        memory_file,
        download_name='amazon_bot_logs.zip',
        as_attachment=True,
        mimetype='application/zip'
    )

@bot_bp.route('/bot/clear-logs', methods=['GET', 'POST'])
@login_required
def clear_logs():
    """Clear bot logs"""
    if not current_user.is_admin:
        flash('You must be an administrator to access this page.', 'danger')
        return redirect(url_for('home'))
    
    # Clear log files
    for log_name, log_path in LOG_FILES.items():
        if os.path.exists(log_path):
            try:
                with open(log_path, 'w') as f:
                    f.write('')
            except Exception as e:
                flash(f'Error clearing {log_name} log: {str(e)}', 'danger')
    
    flash('Logs have been cleared.', 'success')
    return redirect(url_for('bot.view_bot_logs'))

@bot_bp.route('/bot/reset-settings', methods=['POST'])
@login_required
def reset_bot_settings():
    """Reset bot settings to defaults"""
    if not current_user.is_admin:
        flash('You must be an administrator to access this page.', 'danger')
        return redirect(url_for('home'))
    
    save_bot_settings(DEFAULT_SETTINGS.copy())
    flash('Bot settings have been reset to defaults.', 'success')
    return redirect(url_for('bot.bot_settings')) 