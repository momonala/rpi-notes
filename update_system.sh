#!/bin/bash

# Define color codes
GREEN='\033[0;32m'
NO_COLOR='\033[0m'

echo -e "${GREEN}Updating package lists...${NO_COLOR}"
sudo apt-get update -y

echo -e "${GREEN}Upgrading installed packages...${NO_COLOR}"
sudo apt-get upgrade -y

echo -e "${GREEN}Performing full upgrade...${NO_COLOR}"
sudo apt-get dist-upgrade -y

echo -e "${GREEN}Removing unused packages...${NO_COLOR}"
sudo apt-get autoremove -y

echo -e "${GREEN}Cleaning up...${NO_COLOR}"
sudo apt-get clean

echo -e "${GREEN}Firmware update...${NO_COLOR}"
sudo apt full-upgrade


echo -e "${GREEN}Upgrade process completed successfully!${NO_COLOR}"
sudo reboot

