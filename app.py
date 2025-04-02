import os
import json
import traceback
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, g, session
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import trackers
from flask_cors import CORS  # Add CORS support
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from translations import translations

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Security settings - Relaxed for development
app.config.update(
    SECRET_KEY='dev-key-please-change-in-production',  # Fixed secret key for development
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,  # Enable HTTPOnly for security
    SESSION_COOKIE_SAMESITE='Lax',   # Use Lax for better security while still allowing cross-site
    PERMANENT_SESSION_LIFETIME=1800,
    SQLALCHEMY_DATABASE_URI=f'sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), "instance", "amazon_tracker.db"))}',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    WTF_CSRF_ENABLED=False,
    DEBUG=True
)

# Initialize CORS with very permissive settings for development
CORS(app, 
     resources={r"/*": {
         "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],  # Specify allowed origins
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept"],
         "supports_credentials": True,
         "expose_headers": ["Content-Type", "Authorization"],
         "max_age": 3600
     }},
     supports_credentials=True)

# Initialize database and login manager with relaxed settings
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
login_manager.login_message = 'Please log in to access this page.'
login_manager.session_protection = None  # Disable session protection for development

def init_db():
    """Initialize the database and create all tables"""
    # Ensure instance directory exists
    os.makedirs('instance', exist_ok=True)
    
    # Create all tables
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

# Define models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    theme = db.Column(db.String(10), default='light')  # 'light' or 'dark'
    language = db.Column(db.String(2), default='ar')   # 'en' or 'ar', default to Arabic
    products = db.relationship('Product', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    custom_name = db.Column(db.String(200))
    current_price = db.Column(db.Float, nullable=False)
    target_price = db.Column(db.Float)
    image_url = db.Column(db.String(500))
    price_history = db.Column(db.Text, default='[]')  # JSON string of price history
    tracking_enabled = db.Column(db.Boolean, default=True)
    notify_on_any_change = db.Column(db.Boolean, default=False)
    last_checked = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_display_name(self):
        return self.custom_name if self.custom_name else self.name
        
    def get_price_history(self):
        if not self.price_history:
            return []
        
        history = json.loads(self.price_history)
        # Convert string dates to datetime objects
        for entry in history:
            entry['date'] = datetime.fromisoformat(entry['date'])
        
        return history
        
    # Properties for template compatibility
    @property
    def tracking(self):
        return self.tracking_enabled
        
    @property
    def notify_always(self):
        return self.notify_on_any_change

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(500), nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Function to check prices of tracked products
def check_prices():
    with app.app_context():
        products = Product.query.filter_by(tracking_enabled=True).all()
        for product in products:
            try:
                for tracker_method in trackers.all_trackers:
                    try:
                        product_data = tracker_method(product.url)
                        if product_data and product_data.get('price'):
                            new_price = product_data.get('price')
                            
                            # Update price history
                            history = json.loads(product.price_history)
                            history.append({
                                "price": new_price,
                                "date": datetime.utcnow().isoformat()
                            })
                            product.price_history = json.dumps(history)
                            
                            if new_price != product.current_price:
                                if new_price < product.current_price:
                                    notification = Notification(
                                        message=f"Price dropped for {product.get_display_name()} from {product.current_price} ر.س to {new_price} ر.س",
                                        user_id=product.user_id
                                    )
                                    db.session.add(notification)
                                elif product.notify_on_any_change:
                                    notification = Notification(
                                        message=f"Price increased for {product.get_display_name()} from {product.current_price} ر.س to {new_price} ر.س",
                                        user_id=product.user_id
                                    )
                                    db.session.add(notification)
                                
                                if product.target_price and new_price <= product.target_price:
                                    notification = Notification(
                                        message=f"Target price reached for {product.get_display_name()}! Current price: {new_price} ر.س",
                                        user_id=product.user_id
                                    )
                                    db.session.add(notification)
                                
                                product.current_price = new_price
                            
                            product.last_checked = datetime.utcnow()
                            break
                    except Exception as e:
                        continue
            except Exception as e:
                print(f"Error checking price for product {product.id}:")
                traceback.print_exc()
        
        db.session.commit()

@app.before_request
def before_request():
    # Set language based on user preference or default to Arabic
    if current_user.is_authenticated:
        g.lang = current_user.language
        g.theme = current_user.theme
    else:
        g.lang = request.cookies.get('language', 'ar')  # Default to Arabic
        g.theme = request.cookies.get('theme', 'light')

def translate(key):
    return translations[g.lang].get(key, translations['en'].get(key, key))

@app.context_processor
def utility_processor():
    return dict(translate=translate)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, error_message=translate('not_found'), unread_count=0), 404

@app.errorhandler(401)
def unauthorized(e):
    return render_template('error.html', error_code=401, error_message=translate('unauthorized'), unread_count=0), 401

@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', error_code=403, error_message=translate('unauthorized'), unread_count=0), 403

@app.errorhandler(405)
def method_not_allowed(e):
    return render_template('error.html', error_code=405, error_message=translate('method_not_allowed'), unread_count=0), 405

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error_code=500, error_message=translate('server_error'), unread_count=0), 500

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

@app.route('/add_product', methods=['POST'])
@login_required
def add_product():
    try:
        url = request.form.get('url', '').strip()
        custom_name = request.form.get('custom_name', '').strip()
        target_price = request.form.get('target_price', '')
        
        # Validate URL
        if not url:
            return jsonify({"success": False, "error": translate('url_required')})
        
        if not url.startswith('https://www.amazon.sa'):
            return jsonify({"success": False, "error": translate('invalid_url')})
        
        # Check for existing product
        existing_product = Product.query.filter_by(url=url, user_id=current_user.id).first()
        if existing_product:
            return jsonify({"success": False, "error": translate('product_exists')})
        
        # Try to fetch product data
        product_data = None
        fetch_errors = []
        
        for tracker_method in trackers.all_trackers:
            try:
                product_data = tracker_method(url)
                if product_data and product_data.get('price'):
                    break
            except Exception as e:
                fetch_errors.append(str(e))
                continue
        
        if not product_data:
            error_msg = translate('fetch_error')
            print(f"Failed to fetch product data for URL: {url}")
            print("Errors encountered:", fetch_errors)
            return jsonify({"success": False, "error": error_msg})
        
        if not product_data.get('price'):
            error_msg = translate('price_not_found')
            print(f"No price found for product. Data received: {product_data}")
            return jsonify({"success": False, "error": error_msg})
        
        # Create new product
        try:
            product = Product(
                url=url,
                name=product_data.get('name', 'Unknown Product'),
                current_price=product_data.get('price'),
                image_url=product_data.get('image_url'),
                user_id=current_user.id,
                price_history=json.dumps([{
                    "price": product_data.get('price'),
                    "date": datetime.utcnow().isoformat()
                }])
            )
            
            if custom_name:
                product.custom_name = custom_name
            
            if target_price:
                try:
                    product.target_price = float(target_price)
                except ValueError:
                    return jsonify({"success": False, "error": translate('invalid_price')})
            
            db.session.add(product)
            db.session.commit()
            
            # Set success flash message
            session['flash_message'] = {
                'category': 'success', 
                'message': translate('product_added_success').replace('{product_name}', product.get_display_name())
            }
            
            return jsonify({"success": True})
            
        except Exception as e:
            db.session.rollback()
            print(f"Error saving product to database: {str(e)}")
            return jsonify({
                "success": False, 
                "error": translate('save_error')
            })
            
    except Exception as e:
        print(f"Unexpected error in add_product route: {str(e)}")
        return jsonify({
            "success": False, 
            "error": translate('error_occurred')
        })

@app.route('/edit_product/<int:product_id>', methods=['POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if product belongs to current user
    if product.user_id != current_user.id:
        flash(translate('unauthorized_edit'), 'danger')
        return redirect(url_for('home'))
    
    custom_name = request.form.get('custom_name')
    target_price = request.form.get('target_price')
    tracking = request.form.get('tracking') == 'on'
    notify_always = request.form.get('notify_always') == 'on'
    
    if custom_name is not None:
        product.custom_name = custom_name
        
    if target_price:
        try:
            product.target_price = float(target_price)
        except ValueError:
            pass
    else:
        product.target_price = None
    
    product.tracking_enabled = tracking
    product.notify_on_any_change = notify_always
    
    db.session.commit()
    
    flash(f'Product "{product.get_display_name()}" updated successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if product belongs to current user
    if product.user_id != current_user.id:
        flash(translate('unauthorized_delete'), 'danger')
        return redirect(url_for('home'))
        
    db.session.delete(product)
    db.session.commit()
    
    flash(translate('product_deleted_success'), 'success')
    return redirect(url_for('home'))

@app.route('/check_prices', methods=['POST'])
def manual_check_prices():
    check_prices()
    return jsonify({"success": True})

@app.route('/notifications/<int:notification_id>/mark-read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    # Check if notification belongs to current user
    if notification.user_id != current_user.id:
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    notification.read = True
    db.session.commit()
    return jsonify({"success": True})

@app.route('/get_buy_link/<int:product_id>')
def get_buy_link(product_id):
    product = Product.query.get_or_404(product_id)
    referral_code = os.getenv('AMAZON_REFERRAL_CODE', '')
    
    # Add referral code to URL
    if '?' in product.url:
        buy_link = f"{product.url}&tag={referral_code}"
    else:
        buy_link = f"{product.url}?tag={referral_code}"
        
    return redirect(buy_link)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('signup'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('signup'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Account created successfully! Welcome to ZONAR - زونار', 'success')
        return redirect(url_for('home'))
    
    return render_template('signup.html', unread_count=0)

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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(translate('logged_out_success'), 'success')
    return redirect(url_for('login'))

@app.route('/settings/theme', methods=['POST'])
@login_required
def update_theme():
    try:
        theme = request.form.get('theme')
        if theme in ['light', 'dark']:
            current_user.theme = theme
            db.session.commit()
            g.theme = theme  # Update g.theme for the current request
            return jsonify({'status': 'success', 'message': f'The theme has been updated to {theme}'})
        return jsonify({'status': 'error', 'message': 'Invalid theme'}), 400
    except Exception as e:
        print(f"Error updating theme: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to update theme'}), 500

@app.route('/settings/language', methods=['POST'])
@login_required
def update_language():
    language = request.form.get('language')
    if language in ['en', 'ar']:
        current_user.language = language
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Invalid language'}), 400

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

@app.route('/check_price/<int:product_id>', methods=['POST'])
@login_required
def check_single_price(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if product belongs to current user
    if product.user_id != current_user.id:
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    try:
        for tracker_method in trackers.all_trackers:
            try:
                product_data = tracker_method(product.url)
                if product_data and product_data.get('price'):
                    new_price = product_data.get('price')
                    
                    # Update price history
                    history = json.loads(product.price_history)
                    history.append({
                        "price": new_price,
                        "date": datetime.utcnow().isoformat()
                    })
                    product.price_history = json.dumps(history)
                    
                    if new_price != product.current_price:
                        if new_price < product.current_price:
                            notification = Notification(
                                message=f"Price dropped for {product.get_display_name()} from {product.current_price} ر.س to {new_price} ر.س",
                                user_id=product.user_id
                            )
                            db.session.add(notification)
                        elif product.notify_on_any_change:
                            notification = Notification(
                                message=f"Price increased for {product.get_display_name()} from {product.current_price} ر.س to {new_price} ر.س",
                                user_id=product.user_id
                            )
                            db.session.add(notification)
                        
                        if product.target_price and new_price <= product.target_price:
                            notification = Notification(
                                message=f"Target price reached for {product.get_display_name()}! Current price: {new_price} ر.س",
                                user_id=product.user_id
                            )
                            db.session.add(notification)
                        
                        product.current_price = new_price
                    
                    product.last_checked = datetime.utcnow()
                    db.session.commit()
                    return jsonify({"success": True})
            except Exception as e:
                continue
                
        return jsonify({"success": False, "error": "Could not check price"}), 400
    except Exception as e:
        print(f"Error checking price for product {product_id}:")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    try:
        # Initialize database
        init_db()
        
        # Start the scheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(check_prices, 'interval', hours=3)
        scheduler.start()
        
        # Run the app
        port = int(os.environ.get('PORT', 3000))
        print(f"Starting server on port {port}...")
        app.run(
            host='0.0.0.0',
            port=port,
            debug=os.environ.get('FLASK_ENV') == 'development',
            use_reloader=False,  # Disable reloader to avoid scheduler issues
            threaded=True       # Enable threading
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        traceback.print_exc()  # Print full error traceback
        if 'scheduler' in locals() and scheduler.running:
            scheduler.shutdown() 