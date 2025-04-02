"""
This module exists to handle the case where Render tries to import 'your_application.wsgi'.
It simply provides access to our actual app.
"""
from your_application import app

# Make the app available as 'application' which is what WSGI servers expect
application = app 