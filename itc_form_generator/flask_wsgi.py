"""
WSGI entry point for production deployment.

Usage:
    gunicorn wsgi:app -w 4 -b 0.0.0.0:8080

Or for Nest deployment:
    gunicorn wsgi:app -w 4 -b [::]:$PORT
"""

from app import create_app

app = create_app('production')

if __name__ == '__main__':
    app.run()

