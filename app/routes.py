# Routes will be imported from the original app.py file 

import os
import json
import traceback
from datetime import datetime, timedelta
from flask import render_template, request, jsonify, redirect, url_for, flash, g, session
from flask_login import login_user, login_required, logout_user, current_user

from app import app, db, translate
from app.models import User, Product, Notification
import trackers
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_mail import Message
from app import mail
import time

# Routes
@app.route('/')
def home():
    try:
        if current_user.is_authenticated:
            # Redirect to user's dashboard
            return redirect(url_for('user_dashboard'))
        else:
            # Redirect to public home page
            return redirect(url_for('public_home'))
    except Exception as e:
        print(f"Error in home route: {e}")
        traceback.print_exc()
        return redirect(url_for('login'))

@app.route('/public_home')
def public_home():
    try:
        # Get search query
        search_query = request.args.get('search', '').strip()
        
        # Get page number and set items per page
        page = request.args.get('page', 1, type=int)
        per_page = 10  # Maximum 10 products per page as requested
        
        # Get sorting parameter
        sort_by = request.args.get('sort_by', 'discount')  # Default sort by discount
        
        # Base query for all products
        query = Product.query
        
        # Apply search if query exists
        if search_query:
            search_term = f"%{search_query}%"
            query = query.filter(
                db.or_(
                    Product.name.ilike(search_term),
                    Product.custom_name.ilike(search_term)
                )
            )
        
        # Apply sorting
        if sort_by == 'price_low':
            query = query.order_by(Product.current_price.asc())
        elif sort_by == 'price_high':
            query = query.order_by(Product.current_price.desc())
        elif sort_by == 'newest':
            query = query.order_by(Product.created_at.desc())
        else:  # Default: sort by discount percentage (requires special handling)
            # We need to get all products to calculate discount
            all_products = query.all()
            
            # Calculate discount percentage for each product
            products_with_discount = []
            for product in all_products:
                price_history = json.loads(product.price_history)
                
                # Filter out duplicates where price didn't change
                unique_prices = []
                last_price = None
                for entry in price_history:
                    if last_price != entry['price']:
                        unique_prices.append(entry)
                        last_price = entry['price']
                
                # If we have at least 2 price points
                if len(unique_prices) >= 2:
                    # Sort by date, newest first
                    sorted_history = sorted(unique_prices, key=lambda x: x['date'], reverse=True)
                    
                    # Get current and previous prices
                    current_price = product.current_price
                    highest_price = max(entry['price'] for entry in price_history)
                    
                    # Calculate discount percentage
                    if highest_price > current_price:
                        discount_percent = ((highest_price - current_price) / highest_price) * 100
                    else:
                        discount_percent = 0
                    
                    products_with_discount.append((product, discount_percent))
                else:
                    products_with_discount.append((product, 0))  # No discount
            
            # Sort by discount percentage (highest first)
            products_with_discount.sort(key=lambda x: x[1], reverse=True)
            
            # Extract just the products in sorted order
            sorted_products = [p[0] for p in products_with_discount]
            
            # Manual pagination
            total_products = len(sorted_products)
            total_pages = (total_products + per_page - 1) // per_page
            start_idx = (page - 1) * per_page
            end_idx = min(start_idx + per_page, total_products)
            
            paginated_products = sorted_products[start_idx:end_idx]
            
            # Get any unread notifications for authenticated user
            unread_count = 0
            if current_user.is_authenticated:
                notifications = Notification.query.filter_by(
                    user_id=current_user.id, 
                    read=False
                ).all()
                unread_count = len(notifications)
            else:
                notifications = []
            
            # Create a pagination object for template compatibility
            class Pagination:
                def __init__(self, items, page, per_page, total):
                    self.items = items
                    self.page = page
                    self.per_page = per_page
                    self.total = total
                    self.pages = total_pages
                
                def iter_pages(self, left_edge=2, left_current=2, right_current=3, right_edge=2):
                    last = 0
                    for num in range(1, self.pages + 1):
                        if (num <= left_edge or
                            (num > self.page - left_current - 1 and num < self.page + right_current) or
                            num > self.pages - right_edge):
                            if last + 1 != num:
                                yield None
                            yield num
                            last = num
            
            pagination = Pagination(paginated_products, page, per_page, total_products)
            
            return render_template(
                'public_home.html',
                products=pagination,
                notifications=notifications,
                search_query=search_query,
                unread_count=unread_count,
                sort_by=sort_by,
                email_verified=current_user.is_authenticated and current_user.email_verified,
                has_products=total_products > 0
            )
        
        # For non-discount sorting, use standard SQLAlchemy pagination
        products = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Get unread notifications for authenticated users
        unread_count = 0
        if current_user.is_authenticated:
            notifications = Notification.query.filter_by(
                user_id=current_user.id, 
                read=False
            ).order_by(Notification.created_at.desc()).all()
            unread_count = len(notifications)
        else:
            notifications = []
        
        return render_template(
            'public_home.html',
            products=products,
            notifications=notifications,
            search_query=search_query,
            unread_count=unread_count,
            sort_by=sort_by,
            email_verified=current_user.is_authenticated and current_user.email_verified,
            has_products=products.total > 0
        )
    except Exception as e:
        print(f"Error in public_home route: {e}")
        traceback.print_exc()
        return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def user_dashboard():
    try:
        # Check for flash messages in session
        if 'flash_message' in session:
            flash_data = session.pop('flash_message')
            flash(flash_data['message'], flash_data['category'])
        
        # Show email verification reminder if email is not verified
        if not current_user.email_verified:
            flash(translate('verification_required'), 'warning')
        
        # Get search query
        search_query = request.args.get('search', '').strip()
        
        # Get page number from query parameters, default to 1
        page = request.args.get('page', 1, type=int)
        per_page = 5  # Number of products per page
        
        # Base query for user's products
        print(f"Querying products for user ID: {current_user.id}")
        query = Product.query.filter_by(user_id=current_user.id)
        
        # Apply search if query exists
        if search_query:
            search_term = f"%{search_query}%"
            query = query.filter(
                db.or_(
                    Product.name.ilike(search_term),
                    Product.custom_name.ilike(search_term)
                )
            )
        
        # Order by creation date (newest first) and paginate
        products = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        
        # Log product count for debugging
        product_count = query.count()
        print(f"Found {product_count} products for user {current_user.id}")
        
        # For empty state message
        has_products = product_count > 0
        print(f"User has products: {has_products}")
        
        # Get notifications
        notifications = Notification.query.filter_by(
            user_id=current_user.id, 
            read=False
        ).order_by(Notification.created_at.desc()).all()
        
        # Get unread count
        unread_count = len(notifications)
        
        return render_template(
            'index.html',
            products=products,
            notifications=notifications,
            search_query=search_query,
            unread_count=unread_count,
            email_verified=current_user.email_verified,
            has_products=has_products
        )
    except Exception as e:
        print(f"Error in user_dashboard route: {e}")
        traceback.print_exc()
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('home'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            remember = request.form.get('remember', 'off') == 'on'  # Convert checkbox value to boolean
            
            if not username or not password:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': 'Please provide both username and password'})
                flash('Please provide both username and password', 'danger')
                return render_template('login.html', unread_count=0)
                
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                # Check if user already has an active session elsewhere
                if user.session_token and user.session_expiry and user.session_expiry > datetime.utcnow():
                    # Existing session found - handle based on policy
                    if request.form.get('force_login') == 'true':
                        # User has confirmed to force login and invalidate other sessions
                        print(f"Forcing login for {username}, invalidating previous sessions")
                    else:
                        # Alert user about existing session
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return jsonify({
                                'success': False, 
                                'message': translate('session_exists_elsewhere'),
                                'require_confirmation': True
                            })
                        flash(translate('session_exists_elsewhere'), 'warning')
                        return render_template('login.html', unread_count=0, username=username, 
                                              require_confirmation=True)
                
                # Generate a new session token
                session_token = user.generate_session_token()
                
                # Store IP and user agent information
                user.last_ip = request.remote_addr
                user.last_user_agent = request.user_agent.string
                user.last_active = datetime.utcnow()
                
                # Update database
                db.session.commit()
                
                # Improved login with persistent session
                login_user(user, remember=remember)
                session.permanent = True  # Make session permanent
                
                # Store session token in browser cookie
                session['user_session_token'] = session_token
                
                # Set session cookie expiration to 30 days for remembered users
                if remember:
                    from datetime import timedelta
                    app.permanent_session_lifetime = timedelta(days=30)
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': True,
                        'message': 'Logged in successfully!',
                        'redirect': url_for('home')
                    })
                    
                flash('Logged in successfully!', 'success')
                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('home')
                return redirect(next_page)
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': 'Invalid username or password'})
                flash('Invalid username or password', 'danger')
                return render_template('login.html', unread_count=0)
        
        return render_template('login.html', unread_count=0)
    except Exception as e:
        print(f"Error in login route: {e}")
        traceback.print_exc()  # Print full error traceback
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'An error occurred during login. Please try again.'})
        flash('An error occurred during login. Please try again.', 'danger')
        return render_template('login.html', unread_count=0)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    try:
        print("Starting signup process...")
        if current_user.is_authenticated:
            print("User already authenticated, redirecting to home")
            return redirect(url_for('home'))
            
        if request.method == 'POST':
            print("Processing POST request for signup")
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            print(f"Received signup data - Username: {username}, Email: {email}")
            
            # Add some basic validation
            if not username or not email or not password:
                print("Missing required fields")
                flash('Please fill in all fields', 'danger')
                return redirect(url_for('signup'))
            
            # Check for existing username
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                print(f"Username {username} already exists")
                flash('Username already exists', 'danger')
                return redirect(url_for('signup'))
                
            # Check for existing email
            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                print(f"Email {email} already registered")
                flash('Email already registered', 'danger')
                return redirect(url_for('signup'))
            
            print("Creating new user...")
            try:
                user = User(username=username, email=email)
                user.set_password(password)
                
                # Generate verification token
                verification_token = user.generate_verification_token()
                
                print("User object created, adding to session")
                db.session.add(user)
                print("Committing to database")
                db.session.commit()
                print("User saved to database successfully")
                
                # إنشاء رابط تحقق أكثر موثوقية مع معلمة منع التخزين المؤقت
                timestamp = int(datetime.utcnow().timestamp())
                verification_link = url_for('verify_email', token=verification_token, v=timestamp, _external=True)
                print(f"Generated verification link for {email}")
                
                # Send verification email with better tracking and debugging
                print(f"Sending verification email to {email}")
                verification_email_sent = send_localized_email(
                    user,
                    subject_key="verification_email_subject",
                    greeting_key="verification_email_greeting",
                    body_key="verification_email_body",
                    footer_key="verification_email_footer",
                    verification_link=verification_link
                )
                
                if not verification_email_sent:
                    print(f"WARNING: Could not send verification email to {email}. User will need to request a new link.")
                
                # Send welcome email (non-critical, don't worry if it fails)
                print(f"Sending welcome email to {email}")
                welcome_email_sent = send_localized_email(
                    user,
                    subject_key="welcome_email_subject",
                    greeting_key="welcome_email_greeting",
                    body_key="welcome_email_body",
                    footer_key="welcome_email_footer"
                )
                
                if not welcome_email_sent:
                    print(f"WARNING: Could not send welcome email to {email}")
                
                print("Logging in new user")
                login_user(user)
                print("User logged in, redirecting to home")
                
                # Include email verification status in the flash message
                if verification_email_sent:
                    flash(translate('account_created_with_verification'), 'success')
                else:
                    flash(translate('account_created_without_verification'), 'warning')
                
                return redirect(url_for('home'))
            except Exception as inner_e:
                print(f"Error during user creation/database operation: {inner_e}")
                db.session.rollback()  # Roll back the transaction
                traceback.print_exc()
                raise  # Re-raise to be caught by outer try-except
        
        print("Rendering signup template (GET request)")
        return render_template('signup.html', unread_count=0)
    except Exception as e:
        print(f"Error in signup route: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        traceback.print_exc()  # Print full traceback for debugging
        flash('An error occurred during signup. Please try again.', 'danger')
        return render_template('signup.html', unread_count=0)

@app.route('/add_product', methods=['POST'])
@login_required
def add_product():
    try:
        # Double-check that the user is authenticated
        if not current_user.is_authenticated:
            print("User not authenticated but bypassed @login_required - this should not happen")
            return jsonify({
                'success': False, 
                'error': 'Authentication required',
                'redirect': url_for('login')
            }), 401
            
        print("Starting add_product process...")
        
        # Get data from form
        url = request.form.get('url')
        custom_name = request.form.get('custom_name')
        target_price_str = request.form.get('target_price')
        notify_on_any_change = request.form.get('notify_on_any_change') == 'on'
        
        print(f"Product data: URL={url}, Custom name={custom_name}, Target price={target_price_str}, Notify={notify_on_any_change}")
        
        # Validate URL
        if not url:
            print("URL is required but was not provided")
            return jsonify({'success': False, 'error': translate('url_required')})
        
        # Handle shortened Amazon URLs
        import requests
        
        # First, clean the URL (remove spaces, etc.)
        url = url.strip()
        
        # Check for shortened Amazon URLs and remove @ if exists at the beginning
        if url.startswith('@'):
            url = url[1:]
            print(f"Removed @ prefix from URL: {url}")
            
        shortened_url_patterns = [
            'amzn.eu', 'amzn.to', 'amzn.com', 
            'amazon.sa/dp/', 'amazon.sa/gp/', 'amazon.sa/s?'
        ]
        
        is_shortened = any(pattern in url for pattern in shortened_url_patterns)
        
        # If it's a shortened URL, follow redirects to get the full URL
        if is_shortened:
            try:
                print(f"Expanding shortened URL: {url}")
                # Set a user agent to avoid being blocked
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                # Add proper protocol if missing
                if not url.startswith('http'):
                    url = 'https://' + url
                
                # Use GET request to properly handle Amazon's redirects
                response = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
                if response.status_code == 200 or response.status_code == 301 or response.status_code == 302:
                    url = response.url
                    print(f"Expanded URL: {url}")
                else:
                    print(f"Failed to expand URL: Status code {response.status_code}")
            except Exception as e:
                print(f"Error expanding shortened URL: {str(e)}")
                # Continue with original URL if expansion fails
        
        # Validate that it's an Amazon.sa URL after expansion
        valid_amazon_domains = ['amazon.sa', 'www.amazon.sa']
        is_valid_amazon = any(domain in url for domain in valid_amazon_domains)
        
        if not is_valid_amazon:
            print(f"Invalid URL: {url} - not from amazon.sa")
            return jsonify({'success': False, 'error': translate('invalid_url')})
        
        # Check if product already exists for this user
        existing_product = Product.query.filter_by(user_id=current_user.id, url=url).first()
        if existing_product:
            print(f"Product already exists for user {current_user.id}")
            return jsonify({'success': False, 'error': translate('product_exists')})
        
        # Convert target price to float if provided
        target_price = None
        if target_price_str:
            try:
                target_price = float(target_price_str)
                if target_price <= 0:
                    return jsonify({'success': False, 'error': translate('invalid_price')})
            except ValueError:
                return jsonify({'success': False, 'error': translate('invalid_price')})
        
        # Fetch product data from Amazon
        print(f"Fetching product data from Amazon for URL: {url}")
        product_data = trackers.fetch_product_data(url)
        
        if not product_data:
            print("Failed to fetch product data")
            return jsonify({'success': False, 'error': translate('fetch_error')})
        
        if not product_data.get('price'):
            print("No price found for product")
            return jsonify({'success': False, 'error': translate('price_not_found')})
        
        print(f"Product data fetched successfully: {product_data}")
        
        # Create new product
        try:
            # Add price to history
            price_history = [{
                'price': product_data['price'],
                'date': datetime.utcnow().isoformat()
            }]
            
            product = Product(
                url=url,
                name=product_data['name'],
                custom_name=custom_name,
                current_price=product_data['price'],
                target_price=target_price,
                image_url=product_data.get('image_url'),
                local_image=product_data.get('image_binary'),
                image_content_type=product_data.get('image_content_type'),
                last_image_update=datetime.utcnow(),
                tracking_enabled=True,
                notify_on_any_change=notify_on_any_change,
                user_id=current_user.id,
                price_history=json.dumps([{
                    'price': product_data['price'],
                    'date': datetime.utcnow().isoformat()
                }])
            )
            
            db.session.add(product)
            db.session.commit()
            
            # Send email about product tracking if email is verified
            if current_user.email_verified:
                product_name = custom_name or product_data['name']
                print(f"Sending tracking started email for product {product_name} to {current_user.email}")
                send_localized_email(
                    current_user,
                    subject_key="tracking_email_subject",
                    greeting_key="tracking_email_greeting",
                    body_key="tracking_email_body",
                    footer_key="tracking_email_footer",
                    product_name=product_name,
                    current_price=product_data['price']
                )
            else:
                print(f"Email not verified for user {current_user.id}. Skipping email notification.")
                # Add notification in the app to remind user to verify email
                notification = Notification(
                    message=translate('verification_required'),
                    user_id=current_user.id,
                    read=False
                )
                db.session.add(notification)
            
            message = translate('product_added_success').format(product_name=custom_name or product_data['name'])
            print(f"Product added successfully: {message}")
            
            return jsonify({
                'success': True,
                'message': message,
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'custom_name': product.custom_name,
                    'current_price': product.current_price,
                    'target_price': product.target_price,
                    'image_url': product.image_url
                }
            })
        except Exception as e:
            db.session.rollback()
            print(f"Error saving product: {str(e)}")
            traceback.print_exc()
            return jsonify({'success': False, 'error': translate('save_error')})
            
    except Exception as e:
        print(f"Error in add_product route: {str(e)}")
        traceback.print_exc()
        if not current_user.is_authenticated:
            # If error is because user is not logged in, redirect to login page
            return jsonify({
                'success': False, 
                'error': 'Authentication required',
                'redirect': url_for('login')
            }), 401
        return jsonify({'success': False, 'error': 'An unexpected error occurred. Please try again later.'})

@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        # Clear session token
        if hasattr(current_user, 'clear_session_token'):
            current_user.clear_session_token()
            db.session.commit()
            
        # Remove session token from browser session
        if 'user_session_token' in session:
            session.pop('user_session_token')
            
        # Logout the user
        logout_user()
        flash(translate('logged_out_success'), 'success')
    return redirect(url_for('login'))

@app.route('/change_language/<lang>')
def change_language(lang):
    """Force language change with minimal code to avoid bugs"""
    # Force to valid language or default to Arabic
    if lang not in ['ar', 'en']:
        lang = 'ar'
    
    print(f"CHANGING LANGUAGE TO: {lang}")
    
    # Update database for logged in users
    if current_user.is_authenticated:
        current_user.language = lang
        db.session.commit()
    
    # Set everywhere possible
    session['language'] = lang
    session.modified = True
    
    # Prepare response
    response = redirect(request.referrer or url_for('home'))
    
    # Clear any existing cookie first
    response.delete_cookie('language')
    
    # Set with 1 year expiration
    response.set_cookie('language', lang, max_age=31536000)
    
    return response

@app.route('/get_buy_link/<int:product_id>')
@login_required
def get_buy_link(product_id):
    """
    Redirects user to the product URL on Amazon.sa
    Also logs the click for analytics purposes
    """
    try:
        # Verify the product exists and belongs to this user
        product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
        
        # Log the click if needed
        print(f"User {current_user.username} clicked to buy product {product.id}: {product.name}")
        
        # Redirect to the Amazon product URL
        return redirect(product.url)
    except Exception as e:
        print(f"Error in get_buy_link: {str(e)}")
        flash('Unable to access product link', 'danger')
        return redirect(url_for('home'))

@app.route('/edit_product/<int:product_id>', methods=['POST'])
@login_required
def edit_product(product_id):
    """
    Update a product's details based on user input
    """
    try:
        # Verify the product exists and belongs to this user
        product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
        
        # Get form data
        custom_name = request.form.get('custom_name')
        target_price_str = request.form.get('target_price')
        notify_on_any_change = request.form.get('notify_on_any_change') == 'on'
        tracking_enabled = request.form.get('tracking_enabled') == 'on'
        
        print(f"Editing product {product_id}: Custom name={custom_name}, Target price={target_price_str}, Notify={notify_on_any_change}, Tracking={tracking_enabled}")
        
        # Update custom name (if provided)
        if custom_name:
            product.custom_name = custom_name
            
        # Update target price if provided and valid
        if target_price_str:
            try:
                target_price = float(target_price_str)
                if target_price <= 0:
                    flash(translate('invalid_price'), 'danger')
                    return redirect(url_for('home'))
                product.target_price = target_price
            except ValueError:
                flash(translate('invalid_price'), 'danger')
                return redirect(url_for('home'))
        else:
            # Clear target price if empty string was submitted
            product.target_price = None
            
        # Update notification settings
        product.notify_on_any_change = notify_on_any_change
        product.tracking_enabled = tracking_enabled
        
        # Save changes
        db.session.commit()
        flash(translate('product_updated_success'), 'success')
        
        return redirect(url_for('home'))
    except Exception as e:
        print(f"Error in edit_product route: {str(e)}")
        db.session.rollback()
        traceback.print_exc()
        flash(translate('error_occurred'), 'danger')
        return redirect(url_for('home'))

@app.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    """
    Delete a product from the database
    """
    try:
        # Find product and verify ownership
        product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
        
        # Get product name for confirmation message
        product_name = product.custom_name or product.name
        
        # Delete the product
        db.session.delete(product)
        db.session.commit()
        
        # Confirm deletion to user
        flash(translate('product_deleted_success'), 'success')
        print(f"Product {product_id} ({product_name}) deleted successfully by user {current_user.id}")
        
        return redirect(url_for('home'))
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting product {product_id}: {str(e)}")
        traceback.print_exc()
        flash(translate('error_occurred'), 'danger')
        return redirect(url_for('home'))

@app.route('/check_price/<int:product_id>', methods=['POST'])
@login_required
def check_price(product_id):
    try:
        # Get product
        product = Product.query.get_or_404(product_id)
        
        # Check if product belongs to current user
        if product.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Check if the product was checked recently (within the last 15 minutes)
        # Reduced from 1 hour to 15 minutes to allow for more frequent checks
        time_since_last_check = datetime.utcnow() - product.last_checked
        if time_since_last_check < timedelta(minutes=15) and request.args.get('force') != 'true':
            return jsonify({
                'success': False, 
                'error': translate('recently_checked'),
                'last_checked': product.last_checked.isoformat()
            })
        
        # Fetch current price
        product_data = trackers.fetch_product_data(product.url)
        if not product_data or not product_data.get('price'):
            return jsonify({'success': False, 'error': translate('fetch_error')})
        
        # Get the current price
        new_price = product_data.get('price')
        old_price = product.current_price
        price_changed = new_price != old_price
        
        # Record the price change in history
        if price_changed:
            # Add price to history using the new method
            product.add_price_to_history(new_price)
        
        # Update product data
        product.current_price = new_price
        product.last_checked = datetime.utcnow()
        
        # Update image if available (to keep images fresh)
        try:
            if product_data.get('image_binary'):
                product.local_image = product_data.get('image_binary')
                product.image_content_type = product_data.get('image_content_type')
                product.last_image_update = datetime.utcnow()
            # Fallback to image URL if binary not available
            if product_data.get('image_url'):
                product.image_url = product_data.get('image_url')
        except Exception as img_error:
            print(f"Error updating product image: {str(img_error)}")
            # Continue even if image update fails
        
        message = ""
        # Create notification if price changed
        if price_changed:
            # Format price change message
            price_diff = abs(new_price - old_price)
            price_diff_percent = (price_diff / old_price) * 100 if old_price > 0 else 0
            
            if new_price < old_price:
                # Price decreased
                message = translate('price_dropped') + f" {new_price:.2f} SAR (-{price_diff:.2f} SAR, -{price_diff_percent:.1f}%)"
                notification_type = 'price_drop'
            else:
                # Price increased
                message = translate('price_increased') + f" {new_price:.2f} SAR (+{price_diff:.2f} SAR, +{price_diff_percent:.1f}%)"
                notification_type = 'price_increase'
            
            # Create notification for price change if enabled
            if product.notify_on_any_change:
                notification = Notification(
                    user_id=current_user.id,
                    message=message,
                    notification_type=notification_type,
                    related_product_id=product.id
                )
                db.session.add(notification)
            
            # Check target price
            if product.target_price and new_price <= product.target_price and old_price > product.target_price:
                target_message = translate('target_reached') + f" {product.target_price:.2f} SAR"
                target_notification = Notification(
                    user_id=current_user.id,
                    message=target_message,
                    notification_type='target_reached',
                    related_product_id=product.id
                )
                db.session.add(target_notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': translate('price_checked') + (f" - {message}" if message else ""),
            'new_price': new_price,
            'old_price': old_price,
            'price_changed': price_changed,
            'last_checked': product.last_checked.isoformat()
        })
        
    except Exception as e:
        print(f"Error in check_price: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': translate('check_price_error')})

@app.route('/toggle_tracking/<int:product_id>', methods=['POST'])
@login_required
def toggle_tracking(product_id):
    """
    Toggle the tracking status of a product
    """
    try:
        # Verify the product exists and belongs to this user
        product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
        
        # Toggle tracking status
        previous_status = product.tracking_enabled
        product.tracking_enabled = not product.tracking_enabled
        
        # Save changes
        db.session.commit()
        
        # Send email if tracking was just enabled and email is verified
        if not previous_status and product.tracking_enabled:
            if current_user.email_verified:
                print(f"Sending tracking started email for product {product.id} to {current_user.email}")
                product_name = product.custom_name or product.name
                send_localized_email(
                    current_user,
                    subject_key="tracking_email_subject",
                    greeting_key="tracking_email_greeting",
                    body_key="tracking_email_body",
                    footer_key="tracking_email_footer",
                    product_name=product_name,
                    current_price=product.current_price
                )
            else:
                print(f"Email not verified for user {current_user.id}. Skipping email notification.")
                # Add notification in the app to remind user to verify email
                notification = Notification(
                    message=translate('verification_required'),
                    user_id=current_user.id,
                    read=False
                )
                db.session.add(notification)
                db.session.commit()
        
        # Return JSON response for AJAX
        return jsonify({
            'success': True, 
            'tracking': product.tracking_enabled,
            'message': translate('tracking_enabled') if product.tracking_enabled else translate('tracking_disabled')
        })
    except Exception as e:
        print(f"Error toggling tracking for product {product_id}: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': translate('error_occurred')})

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('home'))
            
        if request.method == 'POST':
            email = request.form.get('email')
            
            if not email:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': translate('provide_email')})
                flash(translate('provide_email'), 'danger')
                return render_template('forgot_password.html', unread_count=0)
                
            user = User.query.filter_by(email=email).first()
            
            if user:
                # Generate a reset token
                token = user.generate_reset_token()
                db.session.commit()
                
                # Send password reset email using the refactored function
                reset_url = url_for('reset_password', token=token, _external=True)
                print(f"Sending password reset email to {user.email}")
                
                # Pre-process the footer for HTML to avoid f-string backslash issues
                footer_text = translate('password_reset_footer') if 'password_reset_footer' in translations[g.lang] else "If you didn't request this, please ignore this email."
                footer_html = footer_text.replace('\\\\n', '<br>')
                
                # Create HTML email with reset link and mobile-friendly design
                email_body = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <!-- Arabic Version -->
                    <div dir="rtl" style="text-align: right; background-color: #fff; border-radius: 10px; padding: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                        <h2 style="color: #FF6B00; margin-bottom: 20px;">مرحباً {user.username}،</h2>
                        
                        <p style="margin-bottom: 20px; color: #333; font-size: 16px;">
                            لقد تلقينا طلباً لإعادة تعيين كلمة المرور لحسابك في زونار.
                        </p>
                        
                        <p style="margin-bottom: 20px; color: #333; font-size: 16px;">
                            لإعادة تعيين كلمة المرور، يرجى النقر على الزر أدناه:
                        </p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{reset_url}" style="display: inline-block; background: linear-gradient(135deg, #FF9800, #FF6B00); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px; margin: 20px 0;">
                                إعادة تعيين كلمة المرور
                            </a>
                        </div>
                        
                        <p style="color: #666; font-size: 14px; margin-top: 20px;">
                            إذا لم تتمكن من النقر على الزر، يمكنك نسخ ولصق الرابط التالي في متصفحك:
                        </p>
                        
                        <p style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; word-break: break-all; font-size: 14px;">
                            {reset_url}
                        </p>
                        
                        <p style="color: #666; font-size: 14px;">
                            هذا الرابط صالح لمدة ساعة واحدة فقط. إذا لم تطلب إعادة تعيين كلمة المرور، يرجى تجاهل هذا البريد الإلكتروني.
                        </p>
                        
                        <hr style="border: none; border-top: 1px solid #EEE; margin: 20px 0;">
                        
                        <div style="color: #999; font-size: 12px;">
                            {footer_html}
                        </div>
                        
                        <div style="text-align: center; margin-top: 20px; padding-top: 20px; 
                                  border-top: 1px solid #eee; color: #999; font-size: 12px;">
                            <p>© {datetime.now().year} ZONAR - زونار</p>
                        </div>
                    </div>

                    <!-- English Version -->
                    <div dir="ltr" style="text-align: left; margin-top: 40px; background-color: #fff; border-radius: 10px; padding: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                        <h2 style="color: #FF6B00; margin-bottom: 20px;">Hello {user.username},</h2>
                        
                        <p style="margin-bottom: 20px; color: #333; font-size: 16px;">
                            We received a request to reset your password for your ZONAR account.
                        </p>
                        
                        <p style="margin-bottom: 20px; color: #333; font-size: 16px;">
                            To reset your password, please click the button below:
                        </p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{reset_url}" style="display: inline-block; background: linear-gradient(135deg, #FF9800, #FF6B00); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px; margin: 20px 0;">
                                Reset Password
                            </a>
                        </div>
                        
                        <p style="color: #666; font-size: 14px; margin-top: 20px;">
                            If you can't click the button, copy and paste this link into your browser:
                        </p>
                        
                        <p style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; word-break: break-all; font-size: 14px;">
                            {reset_url}
                        </p>
                        
                        <p style="color: #666; font-size: 14px;">
                            This link is valid for one hour only. If you did not request a password reset, please ignore this email.
                        </p>
                        
                        <hr style="border: none; border-top: 1px solid #EEE; margin: 20px 0;">
                        
                        <div style="color: #999; font-size: 12px;">
                            {footer_html}
                        </div>
                        
                        <div style="text-align: center; margin-top: 20px; padding-top: 20px; 
                                  border-top: 1px solid #eee; color: #999; font-size: 12px;">
                            <p>© {datetime.now().year} ZONAR - زونار</p>
                        </div>
                    </div>
                </div>
                """
                
                # Send the email with HTML content
                msg = Message(
                    subject="إعادة تعيين كلمة المرور - ZONAR Password Reset",
                    recipients=[user.email],
                    html=email_body
                )
                mail.send(msg)
                print(f"Password reset email sent to {user.email}")

                message = translate('reset_email_sent')
                category = 'success'

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': True, 'message': message})
                flash(message, category)

            else:
                # Always inform that email was sent, even if user doesn't exist (security best practice)
                message = translate('reset_email_sent')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': True, 'message': message}) # Pretend success
                flash(message, 'success')
            
            # Redirect back to forgot password page after POST
            return redirect(url_for('forgot_password')) 
        
        # Render template for GET request
        return render_template('forgot_password.html', unread_count=0)
    except Exception as e:
        print(f"Error in forgot_password route: {e}")
        traceback.print_exc()
        flash(translate('error_occurred'), 'danger')
        return render_template('forgot_password.html', unread_count=0)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        if current_user.is_authenticated:
            return redirect(url_for('home'))
            
        if not token:
            flash(translate('invalid_token'), 'danger')
            return redirect(url_for('login'))
            
        # Find user with this token
        user = User.query.filter_by(reset_token=token).first()
        
        if not user or not user.verify_reset_token(token):
            flash(translate('invalid_expired_token'), 'danger')
            return redirect(url_for('forgot_password'))
        
        if request.method == 'POST':
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            if not password or not confirm_password:
                flash(translate('fill_all_fields'), 'danger')
                return render_template('reset_password.html', token=token, unread_count=0)
            
            if password != confirm_password:
                flash(translate('passwords_dont_match'), 'danger')
                return render_template('reset_password.html', token=token, unread_count=0)
            
            # Update the password
            user.set_password(password)
            user.clear_reset_token()
            db.session.commit()
            
            flash(translate('password_updated'), 'success')
            return redirect(url_for('login'))
        
        return render_template('reset_password.html', token=token, unread_count=0)
    except Exception as e:
        print(f"Error in reset_password route: {e}")
        traceback.print_exc()
        flash(translate('error_occurred'), 'danger')
        return redirect(url_for('forgot_password'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    try:
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'update_email':
                email = request.form.get('email')
                password = request.form.get('current_password')
                
                if not email or not password:
                    flash(translate('fill_all_fields'), 'danger')
                    return redirect(url_for('settings'))
                
                # Check if the password is correct
                if not current_user.check_password(password):
                    flash(translate('incorrect_password'), 'danger')
                    return redirect(url_for('settings'))
                
                # Check if email is already in use by another user
                existing_user = User.query.filter_by(email=email).first()
                if existing_user and existing_user.id != current_user.id:
                    flash(translate('email_already_used'), 'danger')
                    return redirect(url_for('settings'))
                
                # Update email
                current_user.email = email
                db.session.commit()
                
                flash(translate('email_updated'), 'success')
                return redirect(url_for('settings'))
                
            elif action == 'update_password':
                current_password = request.form.get('current_password')
                new_password = request.form.get('new_password')
                confirm_password = request.form.get('confirm_password')
                
                if not current_password or not new_password or not confirm_password:
                    flash(translate('fill_all_fields'), 'danger')
                    return redirect(url_for('settings'))
                
                # Check if current password is correct
                if not current_user.check_password(current_password):
                    flash(translate('incorrect_password'), 'danger')
                    return redirect(url_for('settings'))
                
                # Check if new passwords match
                if new_password != confirm_password:
                    flash(translate('passwords_dont_match'), 'danger')
                    return redirect(url_for('settings'))
                
                # Update password
                current_user.set_password(new_password)
                db.session.commit()
                
                flash(translate('password_updated'), 'success')
                return redirect(url_for('settings'))
        
        return render_template('settings.html', unread_count=0)
    except Exception as e:
        print(f"Error in settings route: {e}")
        traceback.print_exc()
        flash(translate('error_occurred'), 'danger')
        return redirect(url_for('home'))

@app.route("/test_email")
@login_required
def test_email():
    try:
        subject = "Zonar Test Email"
        body = f"This is a test email sent from the Zonar app to {current_user.email}."
        if send_email(current_user.email, subject, body):
            flash("Test email sent successfully!", "success")
        else:
            flash("Failed to send test email. Check logs and configuration.", "danger")
        return redirect(url_for('settings'))
    except Exception as e:
        flash(f"Error sending test email: {str(e)}", "danger")
        traceback.print_exc()
        return redirect(url_for('settings'))

def send_email(to, subject, body, html=None):
    """Sends an email using Flask-Mail configuration, with optional HTML content."""
    try:
        # Ensure MAIL_USERNAME and MAIL_PASSWORD are set
        sender = app.config.get('MAIL_USERNAME')
        password = app.config.get('MAIL_PASSWORD')
        
        if not sender or not password:
            print("ERROR: MAIL_USERNAME or MAIL_PASSWORD not configured in Flask app config.")
            # Optionally, you could raise an exception here in production
            return False # Indicate failure

        print(f"Attempting to send email from {sender} to {to} with subject: {subject}")
        
        # Create a more reliable message object with proper encoding
        msg = Message(
            subject=subject,
            recipients=[to],
            body=body,  # Plain text version
            html=html,  # HTML version (if provided)
            sender=sender # Use configured sender
        )
        
        # Attempt to send the email with retry mechanism
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                mail.send(msg)
                print(f"Email sent successfully to {to} (attempt {attempt})")
                return True
            except Exception as retry_error:
                if attempt < max_retries:
                    print(f"Attempt {attempt} failed: {str(retry_error)}. Retrying...")
                    time.sleep(2)  # انتظر قبل المحاولة مرة أخرى
                else:
                    raise  # رمي الاستثناء في المحاولة الأخيرة
                    
    except Exception as e:
        print(f"ERROR sending email to {to}: {str(e)}")
        traceback.print_exc()
        return False

def send_localized_email(user, subject_key, greeting_key, body_key, footer_key, **format_args):
    """Sends localized email using the send_email helper with orange branded HTML template."""
    try:
        lang = user.language if hasattr(user, 'language') and user.language else g.lang
        
        # Translate components
        subject = translate(subject_key).format(username=user.username, **format_args)
        greeting = translate(greeting_key).format(username=user.username, **format_args)
        body_content = translate(body_key).format(**format_args)
        footer = translate(footer_key).format(**format_args)
        
        # Pre-process the content to handle newlines before using in f-strings
        body_content_html = body_content.replace('\\\\n', '<br>')
        footer_html = footer.replace('\\\\n', '<br>')
        
        # Define verification link HTML if present
        verification_link_html = ""
        if 'verification_link' in format_args:
            verification_link_html = f"""
            <div style="text-align: center; margin: 30px 0;">
                <a href="{format_args['verification_link']}" 
                   style="display: inline-block; background: linear-gradient(135deg, #FF9800, #FF6B00); 
                          color: white; padding: 15px 30px; text-decoration: none; 
                          border-radius: 5px; font-weight: bold; font-size: 16px; margin: 20px 0;">
                    {translate('verify_email_button')}
                </a>
            </div>
            <p style="color: #666; font-size: 14px; margin-top: 20px;">
                {translate('if_button_doesnt_work')}
            </p>
            <p style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; 
                      word-break: break-all; font-size: 14px; direction: ltr; text-align: left;">
                {format_args['verification_link']}
            </p>
            """
            
        # Create beautiful HTML email with orange branding
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div dir="{('rtl' if lang == 'ar' else 'ltr')}" style="text-align: {('right' if lang == 'ar' else 'left')}; 
                     background-color: #fff; border-radius: 10px; padding: 20px; 
                     box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                
                <div style="text-align: center; margin-bottom: 20px;">
                    <img src="https://zonar.sa/static/img/logo.png" alt="ZONAR" 
                         style="max-width: 150px; height: auto;"/>
                </div>
                
                <h2 style="color: #FF6B00; margin-bottom: 20px;">{greeting}</h2>
                
                <div style="color: #333; font-size: 16px; line-height: 1.5;">
                    <div style="padding: 20px;">
                        {body_content_html}
                    </div>
                </div>
                
                {verification_link_html}
                
                <hr style="border: none; border-top: 1px solid #EEE; margin: 20px 0;">
                
                <div style="color: #999; font-size: 12px;">
                    {footer_html}
                </div>
                
                <div style="text-align: center; margin-top: 20px; padding-top: 20px; 
                          border-top: 1px solid #eee; color: #999; font-size: 12px;">
                    <p>© {datetime.now().year} ZONAR - زونار</p>
                </div>
            </div>
        </div>
        """
        
        print(f"Preparing localized HTML email for {user.email} (Lang: {lang}) - Subject: {subject}")
        
        # Create plain text version as fallback
        # Avoid f-strings with escape sequences by separating them
        plain_text = f"{greeting}"
        plain_text = plain_text + "\n\n"
        plain_text = plain_text + f"{body_content}"
        plain_text = plain_text + "\n\n"
        plain_text = plain_text + f"{footer}"
        
        if 'verification_link' in format_args:
            verification_text = f"{translate('verify_email_link')}: {format_args['verification_link']}"
            plain_text = plain_text + "\n\n" + verification_text
        
        # Use the central send_email function
        return send_email(user.email, subject, plain_text, html_body)

    except Exception as e:
        print(f"Error preparing or sending localized email for {user.email}: {e}")
        traceback.print_exc()
        return False

@app.route('/verify_email/<token>')
def verify_email(token):
    try:
        print(f"Starting email verification process for token: {token[:10]}...")
        
        # تتبع أفضل للحالات المختلفة
        if not token or len(token) < 10:
            print(f"Invalid token format provided: {token}")
            flash(translate('verification_failed'), 'danger')
            return redirect(url_for('home'))
        
        # إضافة المزيد من التتبع
        print(f"Looking for user with verification token starting with: {token[:10]}...")
        
        # البحث عن المستخدم بواسطة الرمز
        user = User.query.filter_by(verification_token=token).first()
        
        # إذا كان الرمز غير صالح
        if not user:
            print(f"No user found with verification token: {token[:10]}...")
            # محاولة البحث بطريقة أخرى
            print("Trying partial token match...")
            # البحث بالأحرف الأولى من الرمز (قد تكون مشكلة في الرابط)
            users_with_tokens = User.query.filter(User.verification_token.isnot(None)).all()
            for u in users_with_tokens:
                if u.verification_token and u.verification_token.startswith(token[:20]):
                    print(f"Found possible matching user: {u.username} with token starting with {u.verification_token[:10]}")
                    user = u
                    break

            # إذا لم يتم العثور على مستخدم
            if not user:
                print("No matching users found with similar tokens")
                flash(translate('verification_failed'), 'danger')
                return redirect(url_for('home'))
        
        print(f"Found user: {user.username}, Email: {user.email}")
        
        # التحقق من صلاحية الرمز
        if user.verification_token_expiry and datetime.utcnow() > user.verification_token_expiry:
            print(f"Token expired for user: {user.username}")
            flash(translate('verification_failed'), 'danger')
            return redirect(url_for('home'))
        
        # تفعيل البريد الإلكتروني
        print(f"Email verification successful for user: {user.username}")
        user.email_verified = True
        user.verification_token = None
        user.verification_token_expiry = None
        
        # تطبيق التغييرات في قاعدة البيانات
        try:
            db.session.commit()
            flash(translate('verification_success'), 'success')
            
            # إذا لم يكن المستخدم مسجل دخوله، قم بتسجيل دخوله تلقائيًا
            if not current_user.is_authenticated:
                login_user(user)
                flash(translate('logged_in_after_verification'), 'success')
            
            return redirect(url_for('home'))
        except Exception as db_error:
            print(f"Database error during verification: {str(db_error)}")
            db.session.rollback()
            flash(translate('verification_error_try_again'), 'danger')
            return redirect(url_for('home'))
    except Exception as e:
        print(f"Error in verify_email route: {str(e)}")
        traceback.print_exc()
        flash(translate('error_occurred'), 'danger')
        return redirect(url_for('home'))

@app.route('/resend_verification')
@login_required
def resend_verification():
    try:
        print(f"Resend verification requested for user: {current_user.username}, ID: {current_user.id}")
        
        # التحقق إذا كان البريد الإلكتروني مفعل مسبقًا
        if current_user.email_verified:
            print(f"User {current_user.username} already has a verified email")
            flash(translate('email_already_verified'), 'info')
            return redirect(url_for('home'))
        
        # مسح أي رموز سابقة للمستخدم
        current_user.verification_token = None
        current_user.verification_token_expiry = None
        db.session.commit()
        
        # إنشاء رمز تحقق جديد (صالح لمدة 7 أيام)
        verification_token = current_user.generate_verification_token()
        
        try:
            # حفظ التغييرات في قاعدة البيانات
            db.session.commit()
            print(f"Generated new verification token (valid for 7 days) for: {current_user.username}")
            
            # إنشاء رابط التحقق مع معلمة إضافية للإصدار لمنع مشاكل الذاكرة المخبأة
            timestamp = int(datetime.utcnow().timestamp())
            verification_link = url_for('verify_email', token=verification_token, v=timestamp, _external=True)
            
            print(f"Generated verification link for user: {current_user.username}")
            
            # إرسال بريد التحقق باستخدام الوظيفة المعاد تشكيلها
            email_sent = send_localized_email(
                current_user,
                subject_key="verification_email_subject",
                greeting_key="verification_email_greeting",
                body_key="verification_email_body",
                footer_key="verification_email_footer",
                verification_link=verification_link
            )
            
            if email_sent:
                print(f"Verification email sent successfully to: {current_user.email}")
                flash(translate('verification_resent'), 'success')
            else:
                print(f"Failed to send verification email to: {current_user.email}")
                # استعادة التغييرات إذا فشل إرسال البريد
                db.session.rollback()
                flash(translate('email_sending_failed'), 'danger')
        except Exception as db_error:
            print(f"Database error during token generation: {str(db_error)}")
            db.session.rollback()
            flash(translate('error_occurred'), 'danger')
        
        return redirect(url_for('home'))
    except Exception as e:
        print(f"Error in resend_verification route: {str(e)}")
        traceback.print_exc()
        flash(translate('error_occurred'), 'danger')
        return redirect(url_for('home'))

@app.route('/email_testing', methods=['GET', 'POST'])
@login_required
def email_testing():
    """
    Email testing page for users to verify their email settings
    Allows testing different email scenarios (TLS/SSL, languages, etc.)
    """
    result = None
    
    try:
        if request.method == 'POST':
            test_type = request.form.get('test_type')
            email = current_user.email  # Only allow testing with user's own email
            language = request.form.get('language', 'ar')
            connection_type = request.form.get('connection_type', 'tls')
            
            if test_type == 'basic':
                # Basic test email (using current settings)
                result = send_test_basic_email(email)
            
            elif test_type == 'localized':
                # Test with specific language
                result = send_test_localized_email(email, language)
                
            elif test_type == 'verification':
                # Test verification email template
                result = send_test_verification_email(email, language)
                
            elif test_type == 'ssl_tls':
                # Test specific connection method
                result = send_test_connection_email(email, connection_type)
                
            elif test_type == 'direct':
                # Direct SMTP test bypassing Flask-Mail
                result = send_direct_test_email(email, connection_type)
                
            flash(result['message'], result['status'])
            
        return render_template('email_testing.html', unread_count=0)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in email testing page: {str(e)}")
        print(error_trace)
        flash(f"Error: {str(e)}", "danger")
        return render_template('email_testing.html', unread_count=0, error=error_trace)

def send_test_basic_email(receiver_email):
    """Send a basic test email using current settings"""
    try:
        import smtplib, ssl
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import os
        
        # Email settings
        sender_email = os.environ.get("MAIL_USERNAME", "zoonarcom@gmail.com")
        password = os.environ.get("MAIL_PASSWORD", "")
        
        # Create message
        message = MIMEMultipart()
        message["Subject"] = "Basic Test Email from ZONAR"
        message["From"] = sender_email
        message["To"] = receiver_email
        
        # Create body
        body = f"""Hello,

This is a basic test email from ZONAR's maintenance page.
Timestamp: {datetime.utcnow().isoformat()}

If you received this email, it means your basic email configuration is working correctly.

Best regards,
ZONAR Team"""
        
        # Explicitly use UTF-8 encoding for the message
        message.attach(MIMEText(body, "plain", "utf-8"))
        
        # Create a secure context
        context = ssl.create_default_context()
        
        # Get server settings from environment
        mail_server = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
        mail_port = int(os.environ.get("MAIL_PORT", 587))
        mail_use_tls = os.environ.get("MAIL_USE_TLS", "True").lower() in ['true', '1', 't', 'yes', 'y']
        mail_use_ssl = os.environ.get("MAIL_USE_SSL", "False").lower() in ['true', '1', 't', 'yes', 'y']
        
        print(f"Email Config: Server={mail_server}, Port={mail_port}, TLS={mail_use_tls}, SSL={mail_use_ssl}")
        
        # Connect based on configuration
        if mail_use_ssl:
            print("Using SSL connection...")
            with smtplib.SMTP_SSL(mail_server, mail_port, context=context) as server:
                print("Logging in...")
                server.login(sender_email, password)
                print("Sending email...")
                server.sendmail(sender_email, receiver_email, message.as_string())
                print("Email sent successfully")
        else:
            print("Using TLS connection...")
            with smtplib.SMTP(mail_server, mail_port) as server:
                server.ehlo()
                print("Starting TLS...")
                server.starttls(context=context)
                server.ehlo()
                print("Logging in...")
                server.login(sender_email, password)
                print("Sending email...")
                server.sendmail(sender_email, receiver_email, message.as_string())
                print("Email sent successfully")
                
        return {'status': 'success', 'message': f"Basic test email sent to {receiver_email}"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'status': 'danger', 'message': f"Error sending basic test email: {str(e)}"}

def send_test_localized_email(receiver_email, language):
    """Send a test email with localized content"""
    try:
        from translations import translations
        import os
        import smtplib, ssl
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        if language not in ['ar', 'en']:
            language = 'ar'
            
        # Email settings
        sender_email = os.environ.get("MAIL_USERNAME", "zoonarcom@gmail.com")
        password = os.environ.get("MAIL_PASSWORD", "")
        
        # Create message
        message = MIMEMultipart()
        subject = translations[language].get('test_email_subject', "Test Email from ZONAR")
        greeting = translations[language].get('test_email_greeting', "Hello,")
        body_text = translations[language].get('test_email_body', "This is a test email.")
        footer = translations[language].get('test_email_footer', "Best regards, ZONAR Team")
        
        message["Subject"] = subject
        message["From"] = sender_email
        message["To"] = receiver_email
        
        # Combine all parts with some Arabic test text
        email_content = f"""{greeting}

{body_text}
Timestamp: {datetime.utcnow().isoformat()}

Testing Arabic characters: مرحباً بكم في تطبيق زونار

{footer}"""
        
        # Explicitly use UTF-8 for message content
        message.attach(MIMEText(email_content, "plain", "utf-8"))
        
        # Create a secure context
        context = ssl.create_default_context()
        
        # Get server settings from environment
        mail_server = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
        mail_port = int(os.environ.get("MAIL_PORT", 587))
        mail_use_tls = os.environ.get("MAIL_USE_TLS", "True").lower() in ['true', '1', 't', 'yes', 'y']
        mail_use_ssl = os.environ.get("MAIL_USE_SSL", "False").lower() in ['true', '1', 't', 'yes', 'y']
        
        # Send using appropriate method
        if mail_use_ssl:
            with smtplib.SMTP_SSL(mail_server, mail_port, context=context) as server:
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message.as_string())
        else:
            with smtplib.SMTP(mail_server, mail_port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message.as_string())
                
        return {'status': 'success', 'message': f"Localized test email sent to {receiver_email} in {language}"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'status': 'danger', 'message': f"Error sending localized test email: {str(e)}"}

def send_test_verification_email(receiver_email, language):
    """Send a test verification email"""
    try:
        # Create a fake verification link
        verification_link = url_for('home', _external=True) + "?test=verification"
        
        # Create a temporary user object for the send_localized_email function
        class TempUser:
            def __init__(self, email, lang):
                self.email = email
                self.language = lang
                self.username = "TestUser"
                
        temp_user = TempUser(receiver_email, language)
        
        # Send the email
        success = send_localized_email(
            temp_user,
            subject_key="verification_email_subject",
            greeting_key="verification_email_greeting",
            body_key="verification_email_body",
            footer_key="verification_email_footer",
            verification_link=verification_link
        )
        
        if success:
            return {'status': 'success', 'message': f"Verification test email sent to {receiver_email} in {language}"}
        else:
            return {'status': 'danger', 'message': "Failed to send verification test email"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'status': 'danger', 'message': f"Error sending verification test email: {str(e)}"}

def send_test_connection_email(receiver_email, connection_type):
    """Test specific connection method (SSL or TLS)"""
    try:
        import smtplib, ssl
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import os
        
        # Email settings
        sender_email = os.environ.get("MAIL_USERNAME", "zoonarcom@gmail.com")
        password = os.environ.get("MAIL_PASSWORD", "")
        
        # Create message
        message = MIMEMultipart()
        message["Subject"] = f"ZONAR {connection_type.upper()} Connection Test"
        message["From"] = sender_email
        message["To"] = receiver_email
        
        # Create body
        body = f"""Hello,

This is a test email sent using {connection_type.upper()} connection.
Timestamp: {datetime.utcnow().isoformat()}

If you received this email, the {connection_type.upper()} connection is working correctly.

Best regards,
ZONAR Team"""
        
        # Explicitly use UTF-8 encoding
        message.attach(MIMEText(body, "plain", "utf-8"))
        
        # Create a secure context
        context = ssl.create_default_context()
        
        # Use the specified connection type
        mail_server = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
        
        if connection_type.lower() == 'ssl':
            # SSL uses port 465
            with smtplib.SMTP_SSL(mail_server, 465, context=context) as server:
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message.as_string())
        else:
            # TLS uses port 587
            with smtplib.SMTP(mail_server, 587) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message.as_string())
                
        return {'status': 'success', 'message': f"{connection_type.upper()} test email sent to {receiver_email}"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'status': 'danger', 'message': f"Error sending {connection_type.upper()} test email: {str(e)}"}

def send_direct_test_email(receiver_email, connection_type):
    """Send a test email directly using SMTP (bypass any wrapper)"""
    try:
        import smtplib, ssl
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import os
        
        # Hard-coded credentials for direct testing
        # Use environment variables if available
        sender_email = os.environ.get("MAIL_USERNAME", "zoonarcom@gmail.com")
        password = os.environ.get("MAIL_PASSWORD", "")
        mail_server = "smtp.gmail.com"
        
        # Create message with unique subject
        message = MIMEMultipart()
        timestamp = datetime.utcnow().isoformat()
        message["Subject"] = f"ZONAR Direct {connection_type.upper()} Test - {timestamp}"
        message["From"] = sender_email
        message["To"] = receiver_email
        
        # Detailed email body with diagnostic info
        body = f"""Hello,

This is a direct SMTP test email from ZONAR's maintenance page.
Timestamp: {timestamp}

Connection details:
- Method: {connection_type.upper()}
- Server: {mail_server}
- Port: {"465" if connection_type.lower() == 'ssl' else "587"}
- Sender: {sender_email}

This test bypasses Flask-Mail and any other wrappers, using direct SMTP.

Best regards,
ZONAR Team"""
        
        # Explicitly use UTF-8 encoding
        message.attach(MIMEText(body, "plain", "utf-8"))
        
        # Create a secure context
        context = ssl.create_default_context()
        
        # Send using the specified connection type
        if connection_type.lower() == 'ssl':
            # SSL connection
            print(f"Testing direct SSL connection to {mail_server}:465")
            with smtplib.SMTP_SSL(mail_server, 465, context=context) as server:
                print("Server connection established, logging in...")
                server.login(sender_email, password)
                print("Login successful, sending email...")
                server.sendmail(sender_email, receiver_email, message.as_string())
                print("Email sent successfully")
        else:
            # TLS connection
            print(f"Testing direct TLS connection to {mail_server}:587")
            with smtplib.SMTP(mail_server, 587) as server:
                print("Initial connection established, starting TLS...")
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                print("TLS started, logging in...")
                server.login(sender_email, password)
                print("Login successful, sending email...")
                server.sendmail(sender_email, receiver_email, message.as_string())
                print("Email sent successfully")
                
        return {'status': 'success', 'message': f"Direct {connection_type.upper()} test email sent to {receiver_email}"}
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Direct email error: {str(e)}")
        print(error_trace)
        return {'status': 'danger', 'message': f"Error sending direct test email: {str(e)}"}

@app.route('/setup_admin/<token>/<username>')
def setup_admin(token, username):
    """
    Temporary route to set admin access
    Will be removed after initial setup
    """
    import os
    import secrets
    
    # Get the secret token from environment or use a default for testing
    admin_token = os.environ.get('ADMIN_SETUP_TOKEN', 'zonar_temp_token_2024')
    
    if token != admin_token:
        return "Invalid token", 403
        
    try:
        user = User.query.filter_by(username=username).first()
        if not user:
            return f"User {username} not found", 404
            
        user.is_admin = True
        db.session.commit()
        
        return f"""
        <div style="text-align: center; padding: 20px; font-family: Arial, sans-serif;">
            <h2 style="color: #28a745;">Success! ✅</h2>
            <p>User <strong>{username}</strong> is now an admin.</p>
            <p>You can now access the email testing page at:</p>
            <p><a href="/email_testing" style="color: #007bff;">/email_testing</a></p>
            <hr style="margin: 20px 0;">
            <p style="color: #6c757d;">Note: Please bookmark the email testing page URL for future access.</p>
        </div>
        """
    except Exception as e:
        db.session.rollback()
        return f"Error: {str(e)}", 500

@app.route('/save-subscription', methods=['POST'])
@login_required
def save_subscription():
    """حفظ اشتراك الإشعارات الخاص بالمستخدم"""
    try:
        # الحصول على بيانات الاشتراك من طلب JSON
        subscription = request.json
        
        if not subscription:
            return jsonify({'success': False, 'error': 'بيانات الاشتراك غير صالحة'}), 400
            
        # تخزين بيانات الاشتراك في ملف المستخدم
        # يمكن تعديل هذا ليناسب هيكل قاعدة البيانات الخاصة بك
        current_user.push_subscription = json.dumps(subscription)
        current_user.notifications_enabled = True
        db.session.commit()
        
        print(f"تم حفظ اشتراك الإشعارات للمستخدم: {current_user.id}")
        
        return jsonify({'success': True, 'message': 'تم تسجيل الاشتراك بنجاح'})
    except Exception as e:
        print(f"خطأ في حفظ اشتراك الإشعارات: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'حدث خطأ أثناء حفظ الاشتراك'}), 500

@app.route('/send-notification', methods=['POST'])
@login_required
def send_notification():
    """إرسال إشعار للمستخدم لاختبار الإشعارات"""
    try:
        # التحقق من صلاحيات المستخدم (اختياري)
        
        # الحصول على اشتراك الإشعارات للمستخدم
        if not current_user.push_subscription:
            return jsonify({'success': False, 'error': 'المستخدم غير مشترك في الإشعارات'}), 400
            
        subscription_info = json.loads(current_user.push_subscription)
        
        # بيانات الإشعار
        notification_data = {
            'title': 'إشعار اختبار',
            'body': 'هذا إشعار اختباري من زونار',
            'tag': 'test-notification',
            'url': '/'
        }
        
        # إرسال الإشعار عبر webpush
        from pywebpush import webpush, WebPushException
        
        try:
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(notification_data),
                vapid_private_key=app.config.get('VAPID_PRIVATE_KEY'),
                vapid_claims={
                    "sub": "mailto:info@zonar.com"
                }
            )
            
            return jsonify({'success': True, 'message': 'تم إرسال الإشعار بنجاح'})
        except WebPushException as e:
            print(f"خطأ في إرسال الإشعار: {str(e)}")
            # التحقق من حالة الانتهاء
            if e.response and e.response.status_code == 410:
                # الاشتراك لم يعد صالحًا، قم بإزالته
                current_user.push_subscription = None
                db.session.commit()
                return jsonify({'success': False, 'error': 'انتهت صلاحية الاشتراك'}), 410
            return jsonify({'success': False, 'error': f"فشل إرسال الإشعار: {str(e)}"}), 500
    except Exception as e:
        print(f"خطأ في مسار إرسال الإشعار: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'حدث خطأ أثناء إرسال الإشعار'}), 500

@app.route('/offline')
def offline():
    """صفحة وضع عدم الاتصال"""
    return render_template('offline.html', unread_count=0)

@app.route('/change_theme', methods=['POST'])
@login_required
def change_theme():
    """Handle theme change and persist it"""
    try:
        # Get the theme from JSON request
        data = request.get_json()
        theme = data.get('theme', 'light')
        
        if theme not in ['light', 'dark']:
            theme = 'light'
            
        print(f"Changing theme to: {theme}")
        
        # Update user's theme in database
        current_user.theme = theme
        db.session.commit()
        
        # Create response with cookie
        response = jsonify({'success': True, 'theme': theme})
        
        # Set theme cookie with 1 year expiration
        response.set_cookie('theme', theme, max_age=31536000)
        
        return response
    except Exception as e:
        print(f"Error changing theme: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.context_processor
def utility_processor():
    """Make common variables available to all templates"""
    from datetime import datetime
    return {
        'translate': translate,
        'now': datetime.now(),
    }

