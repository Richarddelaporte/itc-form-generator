# Gunicorn configuration for ITC Form Generator

import os
import multiprocessing

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"

# Worker processes
workers = int(os.environ.get('GUNICORN_WORKERS', min(multiprocessing.cpu_count() * 2 + 1, 4)))
worker_class = 'sync'
worker_connections = 1000
timeout = 120  # 2 min timeout for AI parsing

# Logging
accesslog = '-'
errorlog = '-'
loglevel = os.environ.get('LOG_LEVEL', 'info').lower()

# Process naming
proc_name = 'itc_form_generator'

# Server mechanics
preload_app = True
max_requests = 1000
max_requests_jitter = 50
graceful_timeout = 30

