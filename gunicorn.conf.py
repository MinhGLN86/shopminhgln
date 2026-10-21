import os

# Gunicorn configuration cho Cloud Render
port = os.environ.get('PORT', '5000')
bind = f"0.0.0.0:{port}"
workers = 1
threads = 4
timeout = 120
preload_app = False
