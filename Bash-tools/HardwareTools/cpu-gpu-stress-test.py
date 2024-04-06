import subprocess
import time
import os

# Log files
CPU_LOG_FILE = "/var/log/cpu_stress.log"
GPU_LOG_FILE = "/var/log/gpu_temp.log"

# Stress test duration in seconds (10 minutes)
DURATION = 600

# Capture the start timestamp
start_time = time.strftime("%Y-%m-%d-%H:%M:%S")

# Initialize log files with headers and start markers
with open(CPU_LOG_FILE, "a") as cpu_log, open(GPU_LOG_FILE, "a") as gpu_log:
    cpu_log.write(f"CPU_GPU_Testing_Start - {start_time}\n")
    cpu_log.write("date,cpu_temp,fan_speed,pwm_value,watt\n")
    gpu_log.write(f"CPU_GPU_Testing_Start - {start_time}\n")
    gpu_log.write("date,gpu_temp,fan_speed,pwm_value,watt\n")

# Start GPU burn test in Docker for 10 minutes
gpu_burn_process = subprocess.Popen(["docker", "run", "--rm", "--gpus", "1", "gpu_burn"])

# Start the stress-ng test for 10 minutes
stress_process = subprocess.Popen(["stress-ng", "--cpu", "24", "--io", "4", "--vm", "2", "--vm-bytes", "12G", "--timeout", str(DURATION)])

# Read initial energy value for power calculation
with open("/sys/class/powercap/intel-rapl:0/energy_uj", "r") as f:
    initial_energy = int(f.read())
prev_energy = initial_energy

# Monitor and log while either stress-ng or gpu_burn is running
while stress_process.poll() is None or gpu_burn_process.poll() is None:
    date = time.strftime("%Y-%m-%d-%H:%M:%S")
    cpu_temp = subprocess.check_output(["sensors"]).decode()
    cpu_temp = cpu_temp.split("Tctl:")[1].split("°C")[0].strip()
    cpu_fan_speed = int(open("/sys/class/hwmon/hwmon2/fan2_input", "r").read())  # Ensure hwmonX and fanY are correctly identified
    pwm_value = int(open("/sys/class/hwmon/hwmon2/pwm2", "r").read())  # Ensure hwmonX and pwmY are correctly identified

    # Calculate power usage in watts
    with open("/sys/class/powercap/intel-rapl:0/energy_uj", "r") as f:
        current_energy = int(f.read())
    energy_diff = current_energy - prev_energy
    power_usage_watts = energy_diff / 1000000
    prev_energy = current_energy

    # Log CPU metrics with power usage
    with open(CPU_LOG_FILE, "a") as cpu_log:
        cpu_log.write(f"{date},{cpu_temp},{cpu_fan_speed},{pwm_value},{power_usage_watts:.2f}\n")

    time.sleep(2)  # Adjust sleep as necessary

# Capture the end timestamp
end_time = time.strftime("%Y-%m-%d-%H:%M:%S")

# Log the end of the test with the captured timestamp
with open(CPU_LOG_FILE, "a") as cpu_log, open(GPU_LOG_FILE, "a") as gpu_log:
    cpu_log.write(f"CPU_GPU_Testing_Stop - {end_time}\n")
    gpu_log.write(f"CPU_GPU_Testing_Stop - {end_time}\n")