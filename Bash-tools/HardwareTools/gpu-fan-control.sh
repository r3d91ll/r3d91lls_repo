#!/bin/bash

# Fan control settings
pwm_file="/sys/class/hwmon/hwmon2/pwm3"

# Log file path
log_file="/var/log/gpu-fan-control.log"

# Temperature thresholds (adjust as needed)
high_temp_threshold=70
low_temp_threshold=30

# PWM range (adjust based on your fan specifications)
min_pwm=20
max_pwm=255

while true; do
    # Get the current time
    current_time=$(date '+%Y-%m-%d %H:%M:%S')

    # Get the current temperature of the second GPU from nvidia-smi
    gpu_temp=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader --id=1 | awk '{printf "%.0f", $1}')

    # Calculate the desired PWM value based on GPU temperature
    if (( $(echo "$gpu_temp > $high_temp_threshold" | bc -l) )); then
        pwm_value=$max_pwm
    elif (( $(echo "$gpu_temp < $low_temp_threshold" | bc -l) )); then
        pwm_value=$min_pwm
    else
        pwm_value=$(echo "(($gpu_temp - $low_temp_threshold) * ($max_pwm - $min_pwm) / ($high_temp_threshold - $low_temp_threshold) + $min_pwm)" | bc)
    fi

    # Set the new PWM value
    echo "$pwm_value" | sudo tee "$pwm_file" > /dev/null

    # Log current time, GPU temp, and PWM value
    echo "$current_time, GPU Temp: $gpu_temp°C, PWM Value: $pwm_value" | sudo tee -a "$log_file" > /dev/null

    # Delay before checking again
    sleep 2
done
