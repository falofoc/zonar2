"""
Amazon.sa Product Trackers

This module contains different methods to fetch product information from Amazon.sa.
Each tracker method tries a different approach to obtain price, name, and image data.
"""

import re
import json
import time
import random
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# Initialize user agent generator
ua = UserAgent()

def get_random_headers():
    """Generate random headers to avoid bot detection"""
    return {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',  # Added Arabic language preference
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'sec-ch-ua': '"Chromium";v="112", "Google Chrome";v="112", "Not:A-Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1'
    }

def clean_price(price_str):
    """Clean and extract price from string"""
    if not price_str:
        return None
    # Remove currency symbols and whitespace
    price_str = re.sub(r'[^\d.]', '', price_str)
    try:
        return float(price_str)
    except ValueError:
        return None

def get_session():
    """Create a session with proper headers and retry mechanism"""
    session = requests.Session()
    session.headers.update(get_random_headers())
    return session

# Tracker 1: Simple HTML Parser with requests and BeautifulSoup
def tracker_simple_html(url):
    """Fetch product data using a simple GET request and BeautifulSoup parsing"""
    session = get_session()
    response = session.get(url, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'lxml')
    
    # Extract product name
    name_element = soup.select_one('#productTitle')
    name = name_element.text.strip() if name_element else None
    
    # Extract product price - try multiple selectors
    price_selectors = [
        '.a-price .a-offscreen',
        '#priceblock_ourprice',
        '#priceblock_dealprice',
        '.a-color-price',
        '#price_inside_buybox',
        '#corePrice_feature_div .a-price .a-offscreen'
    ]
    
    price = None
    for selector in price_selectors:
        price_element = soup.select_one(selector)
        if price_element:
            price = clean_price(price_element.text)
            if price:
                break
    
    # Extract product image
    image_element = soup.select_one('#landingImage')
    if image_element and 'data-old-hires' in image_element.attrs:
        image_url = image_element['data-old-hires']
    elif image_element and 'src' in image_element.attrs:
        image_url = image_element['src']
    else:
        image_url = None
    
    return {
        'name': name,
        'price': price,
        'image_url': image_url
    }

# Tracker 2: Mobile User Agent Method
def tracker_mobile_agent(url):
    """Fetch product data by pretending to be a mobile device"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
        'sec-ch-ua': '"Safari";v="15.0"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"iOS"'
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    # First visit the main page
    session.get('https://www.amazon.sa/', timeout=10)
    time.sleep(random.uniform(1, 2))
    
    response = session.get(url, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'lxml')
    
    # Extract product name
    name_element = soup.select_one('h1#title, #productTitle')
    name = name_element.text.strip() if name_element else None
    
    # Extract product price - try multiple selectors
    price_selectors = [
        '.a-price .a-offscreen',
        '.a-button-selected .a-color-price',
        '#price_inside_buybox',
        '#corePrice_feature_div .a-price .a-offscreen'
    ]
    
    price = None
    for selector in price_selectors:
        price_element = soup.select_one(selector)
        if price_element:
            price = clean_price(price_element.text)
            if price:
                break
    
    # Extract product image
    image_selectors = [
        'img#main-image',
        'img.a-dynamic-image',
        '#landingImage',
        '#imgBlkFront'
    ]
    
    image_url = None
    for selector in image_selectors:
        image_element = soup.select_one(selector)
        if image_element:
            if 'data-old-hires' in image_element.attrs:
                image_url = image_element['data-old-hires']
            elif 'src' in image_element.attrs:
                image_url = image_element['src']
            if image_url:
                break
    
    return {
        'name': name,
        'price': price,
        'image_url': image_url
    }

# Tracker 3: JSON Data Extraction
def tracker_json_extraction(url):
    """Extract product data from embedded JSON in the page"""
    session = get_session()
    response = session.get(url, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'lxml')
    
    # Try to find price from JSON data blocks
    price = None
    name = None
    image_url = None
    
    # Look for data in script tags
    for script in soup.find_all('script', type='application/json'):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                # Try to find price in various JSON structures
                if 'price' in data:
                    price = clean_price(str(data['price']))
                elif 'selected' in data and isinstance(data['selected'], dict):
                    if 'price' in data['selected']:
                        price = clean_price(str(data['selected']['price']))
                
                # Try to find image URL
                if 'image' in data:
                    image_url = data['image']
                elif 'imageUrl' in data:
                    image_url = data['imageUrl']
                
                if price:
                    break
        except:
            continue
    
    # If we couldn't find data in JSON, try normal HTML parsing
    if not price or not name:
        # Extract product name
        name_element = soup.select_one('#productTitle')
        name = name_element.text.strip() if name_element else None
        
        # Extract product price
        if not price:
            price_element = soup.select_one('.a-price .a-offscreen, #priceblock_ourprice, #priceblock_dealprice')
            if price_element:
                price = clean_price(price_element.text)
    
    # Extract image if not found in JSON
    if not image_url:
        image_element = soup.select_one('#landingImage')
        if image_element:
            image_url = image_element.get('data-old-hires') or image_element.get('src')
    
    return {
        'name': name,
        'price': price,
        'image_url': image_url
    }

# Tracker 4: Delayed Session with Cloudflare Bypass
def tracker_delayed_session(url):
    """Use a session with delays and additional headers to bypass protection"""
    session = get_session()
    
    # Add more realistic headers
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'DNT': '1'
    }
    session.headers.update(headers)
    
    try:
        # Visit homepage first with random delay
        session.get('https://www.amazon.sa/', timeout=10)
        time.sleep(random.uniform(2, 3))
        
        # Add referrer and visit product page
        session.headers.update({'Referer': 'https://www.amazon.sa/'})
        response = session.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Extract all data using comprehensive selectors
        name_element = soup.select_one('#productTitle, h1#title')
        name = name_element.text.strip() if name_element else None
        
        # Updated price selectors for better coverage
        price_selectors = [
            '.a-price .a-offscreen',
            '#priceblock_ourprice',
            '#priceblock_dealprice',
            '.a-color-price',
            '#price_inside_buybox',
            '#corePrice_feature_div .a-price .a-offscreen',
            'span[data-a-color="price"] .a-offscreen',
            '.a-price .a-text-price .a-offscreen',
            '#priceblock_ourprice, #priceblock_dealprice',
            '.a-price .a-text-price span.a-offscreen',
            '.a-price .a-text-price .a-offscreen'
        ]
        
        price = None
        for selector in price_selectors:
            elements = soup.select(selector)
            for element in elements:
                price = clean_price(element.text)
                if price:
                    break
            if price:
                break
        
        # Updated image selectors
        image_selectors = [
            '#landingImage',
            '#imgBlkFront',
            'img#main-image',
            'img.a-dynamic-image',
            '#main-image',
            '#imgBlkFront',
            '#landingImage',
            '.a-dynamic-image'
        ]
        
        image_url = None
        for selector in image_selectors:
            image_element = soup.select_one(selector)
            if image_element:
                # Try different image URL attributes
                image_url = (
                    image_element.get('data-old-hires') or 
                    image_element.get('data-a-dynamic-image', '{}').split('"')[1] or 
                    image_element.get('src') or
                    image_element.get('data-a-dynamic-image', '{}').split('"')[3] or
                    image_element.get('data-a-dynamic-image', '{}').split('"')[5]
                )
                if image_url:
                    break
        
        # If we still don't have data, try JSON extraction
        if not price or not name:
            for script in soup.find_all('script', type='application/json'):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        if not price and 'price' in data:
                            price = clean_price(str(data['price']))
                        if not name and 'title' in data:
                            name = data['title']
                        if not image_url and 'image' in data:
                            image_url = data['image']
                except:
                    continue
        
        return {
            'name': name,
            'price': price,
            'image_url': image_url
        }
    except Exception as e:
        print(f"Error in tracker_delayed_session: {str(e)}")
        return None

# List of all tracker methods to try
all_trackers = [
    tracker_delayed_session,  # Most reliable method
    tracker_mobile_agent,     # Mobile user agent method
    tracker_simple_html,      # Simple HTML parsing
    tracker_json_extraction   # JSON extraction as fallback
]

def fetch_product_data(url):
    """Try all tracker methods until we get valid data"""
    for tracker in all_trackers:
        try:
            data = tracker(url)
            if data and data['name'] and data['price']:
                # Download the image if available
                if data['image_url']:
                    try:
                        image_data, content_type = download_image(data['image_url'])
                        data['image_binary'] = image_data
                        data['image_content_type'] = content_type
                    except Exception as img_error:
                        print(f"Failed to download image: {str(img_error)}")
                        data['image_binary'] = None
                        data['image_content_type'] = None
                return data
        except Exception as e:
            print(f"Error in {tracker.__name__}: {str(e)}")
            continue
    return None

def download_image(image_url):
    """Download image and return as binary data with content type"""
    if not image_url:
        return None, None
        
    # Add a random user agent to avoid blocking
    headers = get_random_headers()
    
    # Make request with timeout and proper headers
    response = requests.get(image_url, headers=headers, timeout=15, stream=True)
    response.raise_for_status()
    
    # Get content type from response headers
    content_type = response.headers.get('Content-Type', 'image/jpeg')
    
    # Return binary image data and content type
    return response.content, content_type 