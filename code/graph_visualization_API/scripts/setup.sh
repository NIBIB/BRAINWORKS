#!/usr/bin/env bash

# ensure the CWD is the directory of this script
script_dir="$(dirname $(realpath $0))"
cd $script_dir

cd ../  # move to main directory

sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install python3-venv -y

# install nginx
echo
echo ----------------
echo INSTALLING NGINX
echo ----------------
echo
sudo apt-get -y install nginx

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt


# install npm
sudo apt-get install npm -y
sudo npm install -y

echo DONE
