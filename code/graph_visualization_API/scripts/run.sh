#!/usr/bin/env bash

# ensure the CWD is the directory of this script
script_dir="$(dirname $(realpath $0))"
cd $script_dir


# Run Nginx with custom config (needs absolute path to config)
sudo systemctl stop nginx  # stop the default nginx process
sudo nginx -c ${script_dir}/../config/nginx.conf

# activate virtual environment
cd ../
source venv/bin/activate

# call gunicorn with config file and log file
sudo pkill gunicorn
gunicorn -c config/gunicorn.conf.py "app:create_app()" &

