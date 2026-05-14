import os

bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
workers = int(os.getenv('GUNICORN_WORKERS', '3'))
threads = int(os.getenv('GUNICORN_THREADS', '4'))
worker_class = 'gthread'
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 60
keepalive = 5
accesslog = '-'
errorlog = '-'
loglevel = 'warning'
capture_output = True
preload_app = True
