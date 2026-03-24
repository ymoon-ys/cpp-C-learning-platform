import os

bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"
workers = int(os.getenv('GUNICORN_WORKERS', '2'))
threads = int(os.getenv('GUNICORN_THREADS', '2'))
worker_class = 'sync'
timeout = 120
keepalive = 5
accesslog = '-'
errorlog = '-'
loglevel = 'info'
capture_output = True
