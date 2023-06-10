# install nginx
sudo apt-get install nginx -y
nginx -c /home/ubuntu/nginx.conf

# install python venv
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install python3-venv -y
python3 -m venv venv  # create venv
source venv/bin/activate  # activate venv
pip install -r requirements.txt  # install python packages

# start gunicorn
nohup gunicorn -c gunicorn_config.py &
