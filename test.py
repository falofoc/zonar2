from app import app, translate
from flask import g

with app.app_context():
    g.lang = 'ar'  # Set language to Arabic
    print(translate('logged_out_success'))
