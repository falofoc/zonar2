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
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Routes
@app.route('/')
def home():
    try:
        if current_user.is_authenticated:
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
                email_verified=current_user.email_verified
            )
        else:
            # For non-authenticated users show login page with proper language support
            print("User not authenticated, showing login page")
            return redirect(url_for('login'))
    except Exception as e:
        print(f"Error in home route: {e}")
        traceback.print_exc()  # Add full traceback for better debugging
        return redirect(url_for('login'))

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
                
                # Generate verification token
                verification_token = user.generate_verification_token()
                
                print("User object created, adding to session")
                db.session.add(user)
                print("Committing to database")
                db.session.commit()
                print("User saved to database successfully")
                
                # Send verification email
                verification_link = url_for('verify_email', token=verification_token, _external=True)
                print(f"Sending verification email to {email}")
                send_localized_email(
                    user,
                    subject_key="verification_email_subject",
                    greeting_key="verification_email_greeting",
                    body_key="verification_email_body",
                    footer_key="verification_email_footer",
                    verification_link=verification_link
                )
                
                # Send welcome email
                print(f"Sending welcome email to {email}")
                send_localized_email(
                    user,
                    subject_key="welcome_email_subject",
                    greeting_key="welcome_email_greeting",
                    body_key="welcome_email_body",
                    footer_key="welcome_email_footer"
                )
                
                print("Logging in new user")
                login_user(user)
                print("User logged in, redirecting to home")
                flash(translate('account_created') + ' ' + translate('verification_required'), 'success')
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

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Handle user logout with proper session cleanup"""
    try:
        # Clear all session data
        session.clear()
        # Logout the user
        logout_user()
        flash(translate('logged_out_success'), 'success')
    except Exception as e:
        print(f"Error during logout: {str(e)}")
        flash(translate('error_occurred'), 'danger')
    
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
    """
    Manually trigger price check for a specific product
    """
    try:
        # Verify the product exists and belongs to this user
        product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
        
        print(f"Manually checking price for product {product_id}: {product.name}")
        
        # Get current product data from Amazon
        product_data = trackers.fetch_product_data(product.url)
        
        if not product_data or 'price' not in product_data:
            print(f"Failed to fetch current price for product {product_id}")
            return jsonify({
                'success': False,
                'error': translate('check_price_error')
            })
        
        # Get the new price
        new_price = product_data['price']
        old_price = product.current_price
        
        # Create price history entry
        price_history = json.loads(product.price_history) if product.price_history else []
        price_history.append({
            'price': new_price,
            'date': datetime.utcnow().isoformat()
        })
        
        # Update product with new price and history
        product.price_history = json.dumps(price_history)
        product.current_price = new_price
        product.last_checked = datetime.utcnow()
        
        # Create notification if price changed and notifications are enabled
        if new_price != old_price:
            if product.notify_on_any_change or (product.target_price and new_price <= product.target_price):
                # Create notification message based on price change
                if new_price < old_price:
                    message = f"{product.custom_name or product.name}: {translate('price_dropped')} {new_price}."
                else:
                    message = f"{product.custom_name or product.name}: {translate('price_increased')} {new_price}."
                
                # If target price reached, add special notification
                if product.target_price and new_price <= product.target_price:
                    message += f" {translate('target_reached')}!"
                
                # Create and save notification
                notification = Notification(
                    message=message,
                    user_id=current_user.id,
                    read=False
                )
                db.session.add(notification)
        
        # Save changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"{translate('current_price')}: {new_price}",
            'old_price': old_price,
            'new_price': new_price
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error checking price for product {product_id}: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': translate('check_price_error')
        })

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
                
                # Send password reset email
                reset_url = url_for('reset_password', token=token, _external=True)
                subject = translate('password_reset')
                
                # Create the email body
                body = f"""
                {translate('reset_email_greeting')} {user.username},
                
                {translate('reset_email_body')}
                
                {reset_url}
                
                {translate('reset_email_expiry')}
                
                {translate('reset_email_footer')}
                """
                
                # Send the email
                from flask_mail import Message
                from app import mail
                
                try:
                    msg = Message(subject=subject, recipients=[user.email], body=body)
                    mail.send(msg)
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({
                            'success': True,
                            'message': translate('reset_email_sent')
                        })
                    flash(translate('reset_email_sent'), 'success')
                except Exception as e:
                    print(f"Email sending error: {e}")
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({
                            'success': False,
                            'message': translate('email_error')
                        })
                    flash(translate('email_error'), 'danger')
            else:
                # Always inform that email was sent, even if user doesn't exist (security best practice)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': True,
                        'message': translate('reset_email_sent')
                    })
                flash(translate('reset_email_sent'), 'success')
            
            return render_template('forgot_password.html', unread_count=0)
        
        return render_template('forgot_password.html', unread_count=0)
    except Exception as e:
        print(f"Error in forgot_password route: {e}")
        traceback.print_exc()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': translate('error_occurred')})
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
        import smtplib, ssl
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import os
        
        # Email settings
        sender_email = os.environ.get("MAIL_USERNAME", "zoonarcom@gmail.com")
        password = os.environ.get("MAIL_PASSWORD", "vnmlzqhuvwktbucj")
        receiver_email = current_user.email
        
        # Create message
        message = MIMEMultipart()
        message["Subject"] = "Test Email from ZONAR"
        message["From"] = sender_email
        message["To"] = receiver_email
        
        # Create body
        body = f"""Hello {current_user.username},

This is a test email from your ZONAR account.

If you received this email, it means your email configuration is working correctly.

Best regards,
ZONAR Team"""
        
        message.attach(MIMEText(body, "plain"))
        
        # Create a secure SSL context
        context = ssl.create_default_context()
        
        # Connect to Gmail SMTP server
        print("Connecting to Gmail...")
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context)
        print("Connected to Gmail")
        
        # Login
        print("Logging in...")
        server.login(sender_email, password)
        print("Login successful")
        
        # Send email
        print("Sending email...")
        server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully")
        
        # Close connection
        server.quit()
        
        flash("Test email sent successfully! Please check your inbox.", "success")
    except Exception as e:
        flash(f"Error sending email: {str(e)}", "danger")
        print(f"Email error: {e}")
    return redirect(url_for("settings"))

def send_localized_email(user, subject_key, greeting_key, body_key, footer_key, **format_args):
    """
    Send an email to a user with localized content based on their language preference
    
    Args:
        user: The user object (must have email and language attributes)
        subject_key: Translation key for the subject
        greeting_key: Translation key for the greeting
        body_key: Translation key for the body
        footer_key: Translation key for the footer
        **format_args: Format arguments to be used in the translations
    """
    try:
        import smtplib, ssl
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import os
        from translations import translations
        
        # Determine the user's language
        user_lang = getattr(user, 'language', 'ar')  # Default to Arabic if not set
        if user_lang not in ['ar', 'en']:
            user_lang = 'ar'  # Default to Arabic if invalid language
        
        # Get email settings from environment
        sender_email = os.environ.get("MAIL_USERNAME", "zoonarcom@gmail.com")
        password = os.environ.get("MAIL_PASSWORD", "vnmlzqhuvwktbucj")
        receiver_email = user.email
        
        # Email server settings
        mail_server = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
        mail_port = int(os.environ.get("MAIL_PORT", 587))
        mail_use_tls = os.environ.get("MAIL_USE_TLS", "True").lower() in ['true', '1', 't', 'yes', 'y']
        mail_use_ssl = os.environ.get("MAIL_USE_SSL", "False").lower() in ['true', '1', 't', 'yes', 'y']
        
        print(f"Email Config: Server={mail_server}, Port={mail_port}, TLS={mail_use_tls}, SSL={mail_use_ssl}")
        print(f"Sending email to {receiver_email} from {sender_email}")
        
        # Get translated content
        subject = translations[user_lang].get(subject_key, translations['en'].get(subject_key, ""))
        greeting = translations[user_lang].get(greeting_key, translations['en'].get(greeting_key, ""))
        body = translations[user_lang].get(body_key, translations['en'].get(body_key, ""))
        footer = translations[user_lang].get(footer_key, translations['en'].get(footer_key, ""))
        
        # Format with provided arguments
        if format_args:
            if "{username}" in greeting:
                greeting = greeting.format(username=user.username, **format_args)
            if any(f"{{{arg}}}" in body for arg in format_args):
                body = body.format(**format_args)
            if any(f"{{{arg}}}" in subject for arg in format_args):
                subject = subject.format(**format_args)
        
        # Create message
        message = MIMEMultipart()
        message["Subject"] = subject
        message["From"] = sender_email
        message["To"] = receiver_email
        
        # Combine all parts
        email_content = f"{greeting}\n\n{body}\n\n{footer}"
        message.attach(MIMEText(email_content, "plain"))
        
        print(f"Email prepared with subject: {subject}")
        
        # Create a secure context
        context = ssl.create_default_context()
        
        # Decide between SSL and TLS based on configuration
        if mail_use_ssl:
            print(f"Using SSL connection on port {mail_port}")
            with smtplib.SMTP_SSL(mail_server, mail_port, context=context) as server:
                print("Logging in to email server...")
                server.login(sender_email, password)
                print("Sending email...")
                server.sendmail(sender_email, receiver_email, message.as_string())
        else:
            print(f"Using TLS connection on port {mail_port}")
            with smtplib.SMTP(mail_server, mail_port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                print("Logging in to email server...")
                server.login(sender_email, password)
                print("Sending email...")
                server.sendmail(sender_email, receiver_email, message.as_string())
        
        print(f"Localized email sent to {user.email} in {user_lang}")
        return True
    except Exception as e:
        import traceback
        print(f"Error sending localized email: {e}")
        traceback.print_exc()  # Print full traceback for debugging
        return False

@app.route('/verify_email/<token>')
def verify_email(token):
    try:
        # Find user with this verification token
        user = User.query.filter_by(verification_token=token).first()
        
        if not user:
            flash(translate('verification_failed'), 'danger')
            return redirect(url_for('home'))
        
        # Check if token is valid
        if not user.verify_verification_token(token):
            flash(translate('verification_failed'), 'danger')
            return redirect(url_for('home'))
        
        # Mark email as verified and clear token
        user.clear_verification_token()
        db.session.commit()
        
        flash(translate('verification_success'), 'success')
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
        if current_user.email_verified:
            flash(translate('email_already_verified'), 'info')
            return redirect(url_for('home'))
        
        # Generate new verification token
        verification_token = current_user.generate_verification_token()
        db.session.commit()
        
        # Send verification email
        verification_link = url_for('verify_email', token=verification_token, _external=True)
        send_localized_email(
            current_user,
            subject_key="verification_email_subject",
            greeting_key="verification_email_greeting",
            body_key="verification_email_body",
            footer_key="verification_email_footer",
            verification_link=verification_link
        )
        
        flash(translate('verification_resent'), 'success')
        return redirect(url_for('home'))
    except Exception as e:
        print(f"Error in resend_verification route: {str(e)}")
        traceback.print_exc()
        flash(translate('error_occurred'), 'danger')
        return redirect(url_for('home'))

