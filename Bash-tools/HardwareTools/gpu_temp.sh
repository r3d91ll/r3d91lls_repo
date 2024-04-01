#!/bin/bash

# Define thresholds for temperature
MIN_TEMP=30
MAX_TEMP=80
# Define PWM values
MIN_PWM=0
MAX_PWM=255

# Get GPU temperature
GPU_TEMP=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader --id=1)

# Calculate PWM value based on GPU_TEMP
# Simple linear scaling for demonstration purposes
if [ "$GPU_TEMP" -le "$MIN_TEMP" ]; then
    PWM_VALUE=$MIN_PWM
elif [ "$GPU_TEMP" -ge "$MAX_TEMP" ]; then
    PWM_VALUE=$MAX_PWM
else
    # Scale PWM value within the temperature range
    RANGE=$(($MAX_TEMP-$MIN_TEMP))
    DELTA=$(($GPU_TEMP-$MIN_TEMP))
    PWM_VALUE=$(($MIN_PWM + ($DELTA * ($MAX_PWM - $MIN_PWM) / $RANGE)))
fi

# Write the calculated PWM value to the fan control
echo $PWM_VALUE > /sys/class/hwmon/hwmonX/pwmY
