#!/bin/bash
source /opt/cas-backup/venv/bin/activate
pip uninstall benji -y 
rm -rf /opt/cas-backup/src/build
rm -rf /opt/cas-backup/src/benji.egg-info
rm -rf /opt/cas-backup/venv/bin/benji*  

cd /opt/cas-backup/
git reset --hard 
git checkout develop
git pull 

source /opt/cas-backup/venv/bin/activate
cd /opt/cas-backup/src
python setup.py install
rm -rf /opt/cas-backup/src/build
rm -rf /opt/cas-backup/src/benji.egg-info

supervisorctl restart all

