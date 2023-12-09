#!/bin/bash

# Check for the correct number of arguments
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <ChangeNumber>"
  exit 1
fi

# Set variables based on the argument
ChangeNumber="$1"
outputDir="/root/$ChangeNumber"
reportFile="$outputDir/post-patch.report"
min_free_space_gb=10  # Set minimum free space requirement in GB
# Check if outputDir exists
if [ ! -d "$outputDir" ]; then
  echo "Directory $outputDir does not exist. Please run the pre-patch script before running this one."
  echo "Pre-patch script location: https://linux-kernels.s3.us-gov-west-1.amazonaws.com/LinuxPrePatchChecks-DNF.sh"
  exit 1
fi

checkDriveSpace() {
  local cache_dir="/var/cache/dnf"  # Default cache directory

  if [ -d "$cache_dir" ]; then
    df_out=$(df -Th "$cache_dir" | awk 'NR==2')
    available_space_gb=$(echo -e "$df_out" | awk '{print int($5)}')
    file_system=$(echo -e "$df_out" | awk '{print $2}')
    mount_point=$(echo -e "$df_out" | awk '{print $NF}')

    if [ "$available_space_gb" -ge "$min_free_space_gb" ]; then
      regular_drive_space_check="QC PASS: $cache_dir has ${available_space_gb}GB of free space."
    else
      regular_drive_space_check="QC FAIL: $cache_dir does not have enough free space for patching (${available_space_gb}G)."

      if [[ "$df_out" == *"/dev/mapper"* ]]; then
        lvm_drive_space_check=$(echo -e "$df_out" | awk -v file_system="$file_system" '{print "LVM is configured for " cache_dir " and is using " file_system}')
        vg_name=$(pvs --noheadings -o vg_name --separator ' ' | awk '{print $1}')
        vg_free_space=$(vgs --noheadings -o vg_free --units g "$vg_name" --separator ' ')
        regular_drive_space_check+="\nVolume Group $vg_name has $vg_free_space free space."
        regular_drive_space_check+="\n$mount_point is using $file_system file system."
      else
        regular_drive_space_check+="\n$mount_point is not using LVM and uses $file_system file system."
      fi
    fi
  else
    cache_dir="/var/cache/yum"  # YUM cache directory
    if [ -d "$cache_dir" ]; then
      df_out=$(df -Th "$cache_dir" | awk 'NR==2')
      available_space_gb=$(echo -e "$df_out" | awk '{print int($5)}')
      file_system=$(echo -e "$df_out" | awk '{print $2}')
      mount_point=$(echo -e "$df_out" | awk '{print $NF}')

      if [ "$available_space_gb" -ge "$min_free_space_gb" ]; then
        regular_drive_space_check="QC PASS: $cache_dir has ${available_space_gb}GB of free space."
      else
        regular_drive_space_check="QC FAIL: $cache_dir does not have enough free space for patching (${available_space_gb}G)."

        if [[ "$df_out" == *"/dev/mapper"* ]]; then
          lvm_drive_space_check=$(echo -e "$df_out" | awk -v file_system="$file_system" '{print "LVM is configured for " cache_dir " and is using " file_system}')
          vg_name=$(pvs --noheadings -o vg_name --separator ' ' | awk '{print $1}')
          vg_free_space=$(vgs --noheadings -o vg_free --units g "$vg_name" --separator ' ')
          regular_drive_space_check+="\nVolume Group $vg_name has $vg_free_space free space."
          regular_drive_space_check+="\n$mount_point is using $file_system file system."
        else
          regular_drive_space_check+="\n$mount_point is not using LVM and uses $file_system file system."
        fi
      fi
    else
      regular_drive_space_check="QC FAIL: The appropriate cache directory is not found. Please provide a valid cache directory."
    fi
  fi
}

checkServiceStatus() {
  local service_name="$1"
  local process_name="$2"
  local pid
  pid=$(pgrep "$process_name")
  if [ -n "$pid" ]; then
    echo -e "$service_name Running"
    systemctl status "$service_name" | grep -q "active (running)"
    if [ $? -ne 0 ]; then
      echo -e "QC FAIL: $service_name is not functional. Manual intervention is required."
    fi
  else
    echo -e "$service_name NOT Running"
    echo "Attempting to start $service_name..."
    systemctl start "$service_name"
    systemctl status "$service_name" | grep -q "active (running)"
    if [ $? -ne 0 ]; then
      echo -e "QC FAIL: $service_name failed to start. Manual intervention is required."
    fi
  fi
}

checkCrowdstrike() {
  cs_pid=$(pgrep falcon)
  if [ -n "$cs_pid" ]; then
    cs_status="Crowdstrike Running"
    cs_version=$(/opt/CrowdStrike/falconctl -g --version 2>/dev/null)
    cs_rfm_state=$(/opt/CrowdStrike/falconctl -g --rfm-state 2>/dev/null)
  else
    cs_status="Crowdstrike NOT Running"
    cs_version="Crowdstrike NOT Running"
    cs_rfm_state="Crowdstrike NOT Running"
  fi
}

checkSplunk() {
  # Capture the full status output
  full_splunk_status=$(/opt/rackspace/splunkforwarder/bin/splunk status)

  if [[ "$full_splunk_status" == *"splunkd is running"* ]]; then
    splunk_status="Splunk Running"
    splunk_last_checkin=$(grep "Connected to idx=" /opt/rackspace/splunkforwarder/var/log/splunk/splunkd.log | tail -n1 | awk '{split($0, a, ""); gsub("idx=|,", "", a[13]); print "Splunk connected to " a[13] " on " a[1] " at " a[2]}')
  elif [[ "$full_splunk_status" == *"splunkd is not running"* ]]; then
    splunk_status="Splunk NOT Running"
    splunk_last_checkin="Splunk NOT Running"
    echo "Attempting to start Splunk..."
    /opt/rackspace/splunkforwarder/bin/splunk enable boot-start --accept-license --answer-yes --no-prompt
    /opt/rackspace/splunkforwarder/bin/splunk start

    # Wait for 1 minute to give Splunk time to start
    sleep 60

    # Recheck the status of splunkd
    splunk_status_after_start=$(/opt/rackspace/splunkforwarder/bin/splunk status)
    if [[ "$splunk_status_after_start" == *"splunkd is running"* ]]; then
      splunk_status="Splunk Running after start attempt"
      splunk_last_checkin=$(grep "Connected to idx=" /opt/rackspace/splunkforwarder/var/log/splunk/splunkd.log | tail -n1 | awk '{split($0, a," "); gsub("idx=|,", "", a[13]); print "Splunk connected to " a[13] " on " a[1] " at " a[2]}')
    else
      splunk_status="Failed to start Splunk"
      echo "WARNING: Splunk did not start successfully."
    fi
  else
    splunk_status="Splunk Status Unknown"
    splunk_last_checkin="Status Check Failed"
  fi
}

# New function: generatePostPatchReport
generatePostPatchReport() {
  mkdir -p "$outputDir"
  {
    echo -e " ##################################### "
    echo -e " Post-Patch Report $(date) "
    echo -e " $HOSTNAME "
    echo -e
    echo -e "### Post-Patch Checks ###"
    echo -e "Check 1: ..."
    echo -e "Check 2: ..."
    echo -e "Check 3: ..."
    echo -e "### End Post-Patch Checks ###"
    echo -e
    echo -e "### Additional Information ###"
    echo -e "Hostname: $HOSTNAME"
    echo -e "Date: $(date)"
    echo -e "### End Additional Information ###"
    echo -e " ##################################### "
  } > "$reportFile"

  # Generate JSON report
  {
    echo -e "{"
    echo -e '  "Post-Patch Report": {'
    echo -e '    "Timestamp": "'$(date -u +%FT%TZ)'",'
    echo -e '    "Hostname": "'$HOSTNAME'",'
    echo -e '    "Post-Patch Checks": {'
    echo -e '      "Check 1": "...",'
    echo -e '      "Check 2": "...",'
    echo -e '      "Check 3": "..."'
    echo -e '    },'
    echo -e '    "Additional Information": {'
    echo -e '      "Hostname": "'$HOSTNAME'",'
    echo -e '      "Date": "'$(date -u +%FT%TZ)'"'
    echo -e '    }'
    echo -e '  }'
    echo -e "}"
  } > "$jsonReportFile"

  # Generate HTML report
  {
    echo -e "[code]"
    echo -e " ##################################### "
    echo -e " Post-Patch Report $(date) "
    echo -e " $HOSTNAME "
    echo -e
    echo -e "### Post-Patch Checks ###"
    echo -e "Check 1: ..."
    echo -e "Check 2: ..."
    echo -e "Check 3: ..."
    echo -e "### End Post-Patch Checks ###"
    echo -e
    echo -e "### Additional Information ###"
    echo -e "Hostname: $HOSTNAME"
    echo -e "Date: $(date)"
    echo -e "### End Additional Information ###"
    echo -e " ##################################### "
    echo -e "[/code]"
  } > "$htmlReportFile"
}

generatePostPatchReport

# Main script logic
cd "$outputDir" || exit
checkSplunk
checkCrowdstrike
generatePostPatchReport
cd "$outputDir"
clear
cat "$reportFile"
