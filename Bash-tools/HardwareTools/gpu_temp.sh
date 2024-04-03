#!/bin/bash

# Define thresholds for temperature
MIN_TEMP=50
MAX_TEMP=85

# Define PWM values
MIN_PWM=0
MAX_PWM=255

# PWM control file
PWM_FILE="/sys/class/hwmon/hwmon2/pwm1"
PWM_ENABLE_FILE="/sys/class/hwmon/hwmon2/pwm1_enable"

# Log file
LOG_FILE="/var/log/gpu_temp.log"

# Function to set PWM control mode
set_pwm_control_mode() {
    local mode=$1
    sudo echo $mode > $PWM_ENABLE_FILE
    if [ $? -ne 0 ]; then
        echo "$(date) - Failed to set PWM control mode to $mode" | sudo tee -a $LOG_FILE
    else
        echo "$(date) - PWM control mode set to $mode" | sudo tee -a $LOG_FILE
    fi
}

# Check and set PWM control mode to manual (1)
current_mode=$(cat $PWM_ENABLE_FILE)
if [ "$current_mode" != "1" ]; then
    set_pwm_control_mode 1
fi

while true; do
    # Get GPU temperature
    GPU_TEMP=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader --id=1)

    # Calculate PWM value based on GPU_TEMP
    if [ "$GPU_TEMP" -le "$MIN_TEMP" ]; then
        PWM_VALUE=$MIN_PWM
    elif [ "$GPU_TEMP" -ge "$MAX_TEMP" ]; then
        PWM_VALUE=$MAX_PWM
    else
        # Scale PWM value within the temperature range
        RANGE=$(($MAX_TEMP - $MIN_TEMP))
        DELTA=$(($GPU_TEMP - $MIN_TEMP))
        PWM_VALUE=$(($MIN_PWM + ($DELTA * ($MAX_PWM - $MIN_PWM) / $RANGE)))
    fi

    # Write the calculated PWM value to the fan control
    echo $PWM_VALUE | sudo tee $PWM_FILE > /dev/null
    if [ $? -ne 0 ]; then
        echo "$(date) - Failed to write PWM value to $PWM_FILE" | sudo tee -a $LOG_FILE
    else
        echo "$(date) - PWM value set to $PWM_VALUE" | sudo tee -a $LOG_FILE
    fi

    # Wait for a short interval before the next iteration
    sleep 5
done
