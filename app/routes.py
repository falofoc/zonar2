# Routes will be imported from the original app.py file 

import os
import json
import traceback
from datetime import datetime
from flask import render_template, request, jsonify, redirect, url_for, flash, g, session
from flask_login import login_user, login_required, logout_user, current_user

from app import app, db, translate
from app.models import User, Product, Notification
import trackers

# Routes
@app.route('/')
def home():
    try:
        if current_user.is_authenticated:
            # Check for flash messages in session
            if 'flash_message' in session:
                flash_data = session.pop('flash_message')
                flash(flash_data['message'], flash_data['category'])
            
            # Get search query
            search_query = request.args.get('search', '').strip()
            
            # Get page number from query parameters, default to 1
            page = request.args.get('page', 1, type=int)
            per_page = 5  # Number of products per page
            
            # Base query for user's products
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
                unread_count=unread_count
            )
        else:
            return render_template('login.html', unread_count=0)
    except Exception as e:
        print(f"Error in home route: {e}")
        return render_template('login.html', unread_count=0)

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('home'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            remember = request.form.get('remember', False)
            
            if not username or not password:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': 'Please provide both username and password'})
                flash('Please provide both username and password', 'danger')
                return render_template('login.html', unread_count=0)
                
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                login_user(user, remember=bool(remember))
                session.permanent = True  # Make session permanent
                
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
                print("User object created, adding to session")
                db.session.add(user)
                print("Committing to database")
                db.session.commit()
                print("User saved to database successfully")
                
                print("Logging in new user")
                login_user(user)
                print("User logged in, redirecting to home")
                flash('Account created successfully! Welcome to ZONAR - زونار', 'success')
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
        
        # Validate Amazon.sa URL
        if not url.startswith('https://www.amazon.sa'):
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
            product = Product(
                url=url,
                name=product_data['name'],
                custom_name=custom_name,
                current_price=product_data['price'],
                target_price=target_price,
                image_url=product_data.get('image_url'),
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
@login_required
def logout():
    logout_user()
    flash(translate('logged_out_success'), 'success')
    return redirect(url_for('login'))

@app.route('/change_language/<lang>')
def change_language(lang):
    if lang in ['en', 'ar']:
        if current_user.is_authenticated:
            current_user.language = lang
            db.session.commit()
        
        # Set a cookie for all users (including non-authenticated)
        response = redirect(request.referrer or url_for('home'))
        response.set_cookie('language', lang)
        return response
    return redirect(request.referrer or url_for('home')) 