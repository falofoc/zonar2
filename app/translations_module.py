"""
Dedicated module for handling translations to avoid circular imports.
"""
import os
import sys

# Ensure parent directory is in path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import translations safely
try:
    # Try to import the translations dictionary directly
    from translations import translations
except ImportError as e:
    # If that fails, try to import it as a module
    try:
        import translations
        translations = translations.translations
    except (ImportError, AttributeError):
        # As a fallback, create a basic translation dictionary
        print(f"ERROR IMPORTING TRANSLATIONS: {e}")
        translations = {
            'en': {
                'app_name': 'Amazon.sa Price Tracker',
                'login': 'Login',
                'signup': 'Sign Up',
                'logout': 'Logout',
                'notifications': 'Notifications',
                'add_product': 'Add Product',
                'english': 'English',
                'arabic': 'العربية',
            },
            'ar': {
                'app_name': 'متتبع أسعار أمازون السعودية',
                'login': 'تسجيل الدخول',
                'signup': 'إنشاء حساب',
                'logout': 'تسجيل الخروج',
                'notifications': 'الإشعارات',
                'add_product': 'إضافة منتج',
                'english': 'English',
                'arabic': 'العربية',
            }
        }
        print("Using fallback translations dictionary")

def get_translations():
    """
    Returns the translations dictionary.
    """
    return translations 