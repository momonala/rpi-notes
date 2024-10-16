#!/bin/bash

# Get CPU usage
cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')

# Get memory usage
mem_total=$(free | grep Mem | awk '{print $2}')
mem_used=$(free | grep Mem | awk '{print $3}')
mem_usage=$(awk "BEGIN {printf \"%.2f\", $mem_used/$mem_total*100}")

# Convert memory total to human-readable format
mem_total_human=$(numfmt --to=iec-i --suffix=B $mem_total)
mem_used_human=$(numfmt --to=iec-i --suffix=B $mem_used)  # Convert mem_used to human-readable format

# Get total and available disk space in GB
total_space=$(df -h / | grep / | awk '{print $2}')
available_space=$(df -h / | grep / | awk '{print $4}')
disk_total=$(df / | grep / | awk '{print $2}')
disk_used=$(df / | grep / | awk '{print $3}')
disk_usage=$(awk "BEGIN {printf \"%.2f\", $disk_used/$disk_total*100}")

# Get uptime
uptime=$(uptime -p)

# Get Raspberry Pi temperature
temp_raw=$(cat /sys/class/thermal/thermal_zone0/temp)
temp_celsius=$(echo "scale=1; $temp_raw / 1000" | bc)

# Print results
LIGHT_BLUE='\033[1;34m'
NO_COLOR='\033[0m'

echo -e "${LIGHT_BLUE}CPU Usage:${NO_COLOR} ${cpu_usage}%"
echo -e "${LIGHT_BLUE}Memory Usage:${NO_COLOR} ${mem_usage}% (${mem_used_human}/${mem_total_human})"  # Use human-readable mem_used
echo -e "${LIGHT_BLUE}Disk Space Usage:${NO_COLOR} ${disk_usage}% (free:${available_space}/${total_space})"
echo -e "${LIGHT_BLUE}Uptime:${NO_COLOR} ${uptime}"
echo -e "${LIGHT_BLUE}Temperature:${NO_COLOR} ${temp_celsius}°C"
