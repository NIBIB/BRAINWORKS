#!/bin/bash

#####################################################
# BRAINWORKS - Cluster Computing Setup Script
# When run on an Unbuntu 20.04 portal machine, this
# script will configure the machine with all requirements
# needed to run the NLP pipeline of BRAINWORKS
#####################################################

######################################################
# 1. Update the Machine and install Python dependencies
######################################################
sudo apt-get update -y
sudo apt-get net-tools
sudo apt-get install python3.8-venv -y
sudo apt install libcairo2-dev pkg-config python3-dev -y


######################################################
# 2. Create output directory structure
######################################################
mkdir output; mkdir output/out; mkdir output/err
mkdir module_src; mkdir module_src/java

######################################################
# 3. Install Java Dependencies
######################################################
cd module_src/java
wget https://download.oracle.com/java/17/archive/jdk-17.0.1_linux-x64_bin.tar.gz
tar zxvf jdk-17.0.1_linux-x64_bin.tar.gz
rm *.tar.gz
cd ../../  # back out to cluster/
cp -r privatemodules ~/privatemodules  # copy privatemodules to the home directory

######################################################
# 3. Create and bind to python virtual environemnt
######################################################
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install setuptools==44.0.0
pip install fsspec==2021.9.0
pip install datasets==1.12.1
pip install wheel==0.34.2
pip install allennlp==2.7.0
pip install allennlp-models==2.7.0
pip install -r ../requirements/cluster_requirements.txt
python3 -c "import stanza; stanza.install_corenlp()"

