#!/bin/bash

# Bold cyan divider
DIVIDER="\033[1;36m----------------------------------------\033[0m"

# Get matching services
services=$(systemctl list-units --type=service 'projects_*' --no-legend | awk '{print $1}')

if [ -z "$services" ]; then
  echo "No matching services found."
  exit 0
fi

for svc in $services; do
  desc=$(systemctl show -p Description --value "$svc")
  echo -e "$DIVIDER"
  echo -e "\033[1;33m$svc\033[0m - $desc"
  echo "journalctl -u $svc -f -n 100"
  echo "sudo systemctl restart $svc"
done
