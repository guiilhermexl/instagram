#!/bin/bash
sudo apt-get update
sudo apt-get install -y wget unzip xvfb
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
pip install -r requirements.txt
