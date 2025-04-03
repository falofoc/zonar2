-- Create users table
CREATE TABLE IF NOT EXISTS public.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    language VARCHAR(2) DEFAULT 'ar',
    theme VARCHAR(10) DEFAULT 'light',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reset_token VARCHAR(100),
    reset_token_expiry TIMESTAMP,
    verification_token VARCHAR(100),
    verification_token_expiry TIMESTAMP,
    email_verified BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,
    push_subscription TEXT,
    notifications_enabled BOOLEAN DEFAULT FALSE,
    device_info TEXT
);

-- Create products table
CREATE TABLE IF NOT EXISTS public.products (
    id SERIAL PRIMARY KEY,
    url VARCHAR(500) NOT NULL,
    name VARCHAR(200) NOT NULL,
    custom_name VARCHAR(200),
    current_price FLOAT NOT NULL,
    target_price FLOAT,
    image_url VARCHAR(500),
    price_history TEXT DEFAULT '[]',
    tracking_enabled BOOLEAN DEFAULT TRUE,
    notify_on_any_change BOOLEAN DEFAULT FALSE,
    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create notifications table
CREATE TABLE IF NOT EXISTS public.notifications (
    id SERIAL PRIMARY KEY,
    message VARCHAR(500) NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER NOT NULL REFERENCES public.users(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_products_user_id ON public.products(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON public.notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON public.notifications(read);
CREATE INDEX IF NOT EXISTS idx_products_tracking_enabled ON public.products(tracking_enabled); 