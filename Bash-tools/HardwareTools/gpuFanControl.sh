#!/bin/bash


## This version is for the ASRock AB350 K1

# Path to the hwmon device and fan control file
hwmon_path="/sys/class/hwmon/hwmon1"
fan_control_file="$hwmon_path/pwm5"
fan_speed_input_file="$hwmon_path/fan5_input"

# Log file path
log_file="/var/log/gpu-fan-control.log"

# Temperature thresholds (adjust as needed)
high_temp_threshold=70
low_temp_threshold=60

# Fan speed adjustment step (percentage) and minimum fan speed
fan_speed_step=10
min_fan_speed=75

while true; do
    # Get the current time
    current_time=$(date '+%Y-%m-%d %H:%M:%S')

    # Get the current GPU temperature
    gpu_temp=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader)

    # Read the current fan speed
    current_fan_speed=$(cat "$fan_speed_input_file")

    # Check if the temperature exceeds the high threshold
    if [ "$gpu_temp" -gt "$high_temp_threshold" ]; then
        # Calculate new speed
        new_speed=$((current_fan_speed + (current_fan_speed * fan_speed_step / 100)))
        echo "$new_speed"
    elif [ "$gpu_temp" -lt "$low_temp_threshold" ]; then
        # Calculate new speed
        new_speed=$((current_fan_speed - (current_fan_speed * fan_speed_step / 100)))
        echo "$new_speed"
    else
        new_speed=$current_fan_speed
    fi

    # Ensure new speed is not below minimum
    if [ "$new_speed" -lt "$min_fan_speed" ]; then
        new_speed=$min_fan_speed
    fi

    # Apply the new fan speed
    echo "$new_speed" | sudo tee "$fan_control_file" > /dev/null

    # Log current time, GPU temp, and fan speed
    echo "$current_time, GPU Temp: $gpu_temp°C, Fan Speed: $new_speed" | sudo tee -a "$log_file" > /dev/null

    # Delay before checking again
    sleep 2
done
