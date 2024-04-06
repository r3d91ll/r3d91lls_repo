#!/bin/bash

# Define the log file for power usage
POWER_LOG_FILE="/var/log/power_usage.log"

# Duration for powerstat monitoring in seconds
DURATION=600

# Define a temporary file to capture powerstat's output
TEMP_FILE="/tmp/powerstat_output.tmp"

# Ensure the temporary file is cleaned up on script exit
trap "rm -f $TEMP_FILE" EXIT

# Start logging header for CSV
echo "date,power_usage" | sudo tee -a $POWER_LOG_FILE

# Run powerstat in the background to monitor power usage
# -R for raw data, 1 for 1 second interval
powerstat -R 1 $DURATION > $TEMP_FILE &

# Capture the PID of powerstat for later monitoring
POWERSTAT_PID=$!

# Monitor and log power usage
while [ $(ps -p $POWERSTAT_PID -o comm=) ]; do
    # Get the latest power usage value
    POWER_USAGE=$(tail -1 $TEMP_FILE | awk '{print $NF}')
    
    # Check for numeric value to ensure it's a valid power reading
    if [[ $POWER_USAGE =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
        DATE=$(date +%Y-%m-%d-%H:%M:%S)
        echo "$DATE,$POWER_USAGE" | sudo tee -a $POWER_LOG_FILE
    fi
    
    sleep 5
done
