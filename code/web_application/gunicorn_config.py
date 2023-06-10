bind = "0.0.0.0:8000"   # where gunicorn serves the flask app
workers = 1  # how many gunicorn workers at once
timeout = 600
wsgi_app = "flask_app:create_app('config.RedShiftConfig')"  # where gunicorn gets the app from
