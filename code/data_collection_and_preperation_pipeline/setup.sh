sudo apt-get update -y
sudo apt-get install python3.8-venv -y
sudo apt install python3-dev -y
sudo apt install awscli -y

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install wheel
pip install -r requirements/lightsail_requirements.txt
# python setup.py install  # install local CLI  # TODO for some reason this creates some import errors that don't happen when using pip install -e

# Install Node.js to use pcluster
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.38.0/install.sh | bash
chmod ug+x ~/.nvm/nvm.sh
source ~/.nvm/nvm.sh
nvm install --lts

