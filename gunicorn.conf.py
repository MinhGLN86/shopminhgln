import os

# Gunicorn configuration
port = os.environ.get('PORT', '5000')
bind = f"0.0.0.0:{port}"
workers = 2
threads = 2
timeout = 120
