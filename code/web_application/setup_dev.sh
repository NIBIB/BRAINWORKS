
# install NPM 18 for debian systems
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install nodejs -y

# install python venv
sudo apt-get install python3-venv -y
python3 -m venv venv  # create venv
source venv/bin/activate  # activate venv
pip install -r requirements.txt  # install python packages

cd react-app
npm install  # install node packages
cd ../