#!/bin/bash

ChangeNumber="$1"
outputDir="/root/$ChangeNumber"
kernelPackageFile="$outputDir/kernel_packages"
reportFile="$outputDir/pre-patch.report"
jsonReportFile="$outputDir/pre-patch.json"
htmlReportFile="$outputDir/pre-patch.html"
min_free_space_gb=3

checkDriveSpace() {
  local cache_dir="/var/cache/apt"  # Package manager cache directory

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
    systemctl status falcon-sensor | grep -q "active (running)"
    if [ $? -ne 0 ]; then
      echo -e "QC FAIL: Crowdstrike is not functional. Manual intervention is required."
    fi
  else
    cs_status="Crowdstrike NOT Running"
    cs_version="Crowdstrike NOT Running"
    echo "Attempting to start Crowdstrike..."
    systemctl start falcon-sensor
    systemctl status falcon-sensor | grep -q "active (running)"
    if [ $? -ne 0 ]; then
      echo -e "QC FAIL: Crowdstrike failed to start. Manual intervention is required."
    fi
  fi
}

checkSplunk() {
  # Get the status of splunkd
  splunk_status=$(/opt/rackspace/splunkforwarder/bin/splunk status | grep "splunkd")

  if [[ "$splunk_status" == *"splunkd is running"* ]]; then
    splunk_last_checkin=$(grep "Connected to idx=" /opt/rackspace/splunkforwarder/var/log/splunk/splunkd.log | tail -n1 | awk '{split($0, a, " "); gsub("idx=|,", "", a[13]); print "Splunk connected to " a[13] " on " a[1] " at " a[2]}')
  else
    splunk_status="Splunk NOT Running"
    splunk_last_checkin="Splunk NOT Running"
    echo "Attempting to start Splunk..."
    /opt/rackspace/splunkforwarder/bin/splunk enable boot-start --accept-license --answer-yes --no-prompt
    /opt/rackspace/splunkforwarder/bin/splunk start

    # Wait for 1 minute to give Splunk time to start
    sleep 60

    # Recheck the status of splunkd
    splunk_status_after_start=$(/opt/rackspace/splunkforwarder/bin/splunk status | grep "splunkd")
    if [[ "$splunk_status_after_start" == *"splunkd is running"* ]]; then
      splunk_status="Splunk Running after start attempt"
      splunk_last_checkin=$(grep "Connected to idx=" /opt/rackspace/splunkforwarder/var/log/splunk/splunkd.log | tail -n1 | awk '{split($0, a, " "); gsub("idx=|,", "", a[13]); print "Splunk connected to " a[13] " on " a[1] " at " a[2]}')
    else
      splunk_status="Failed to start Splunk"
      echo "WARNING: Splunk did not start successfully."
    fi
  fi
}

generatePrePatchReport() {
  mkdir -p "$outputDir"
  {
    echo -e " ##################################### "
    echo -e " Pre-Patch Report $(date) "
    echo -e " $HOSTNAME "
    echo -e
    echo -e "### PCM Services Checks ###"
    echo -e "BigFix agent: $(checkServiceStatus "BigFix BESClient" "BESClient")"
    echo -e "ScaleFT agent: $(checkServiceStatus "ScaleFT sftd" "sftd")"
    echo -e "Qualys agent: $(checkServiceStatus "Qualys qualys" "qualys")"
    echo -e "Splunk agent: $splunk_status"
    echo -e "    $splunk_last_checkin"
    echo -e "EnCase agent: $(checkServiceStatus "EnCase enlinux" "enlinux")"
    echo -e "Crowdstrike agent: $cs_status"
    echo -e "    Crowdstrike Version: $cs_version"
    echo -e "    Crowdstrike RFM State: $cs_rfm_state"
    echo -e "### End PCM Services Checks ###"
    echo -e
    echo -e "### Repositories ###"
    echo -e "Repositories"
    apt-cache policy | grep "http" | awk '{print $2}' | sort -u
    echo -e "### End Repositories###"
    echo -e
    echo -e "### Kernel Information ###"
    echo -e "Currently running kernel version is: $(uname -r)"
    echo -e
    echo -e "Available Kernels"
    apt-cache policy linux-image-* | grep "Candidate" | awk '{print $2}' | sort -u
    echo -e "Installed Kernel packages"
    dpkg -l linux-image-* | grep '^ii' | awk '{print $2}' | sed 's/-[0-9].*$//' | sort -u > /tmp/kernelPackageFile
    cat /tmp/kernelPackageFile | sort -u | tee "$kernelPackageFile"
    echo -e "### END Kernel Information ###"
    echo -e
    echo -e "### Drive Space Checks ###"
    echo -e "$regular_drive_space_check"
    echo -e
    echo -e "### END Pre-Patch Report ###"
    echo -e " ##################################### "

  } > "$reportFile"

  # Generate JSON report
  {
    echo -e "{"
    echo -e '  "Pre-Patch Report": {'
    echo -e '    "Timestamp": "'$(date -u +%FT%TZ)'",'
    echo -e '    "Hostname": "'$HOSTNAME'",'
    echo -e '    "PCM Services Checks": {'
    echo -e '      "BigFix agent": "'$(checkServiceStatus "BigFix BESClient" "BESClient")'",'
    echo -e '      "ScaleFT agent": "'$(checkServiceStatus "ScaleFT sftd" "sftd")'",'
    echo -e '      "Qualys agent": "'$(checkServiceStatus "Qualys qualys" "qualys")'",'
    echo -e '      "Splunk agent": "'$splunk_status'",'
    echo -e '      "Splunk Last Checkin": "'$splunk_last_checkin'",'
    echo -e '      "EnCase agent": "'$(checkServiceStatus "EnCase enlinux" "enlinux")'",'
    echo -e '      "Crowdstrike agent": "'$cs_status'",'
    echo -e '      "Crowdstrike Version": "'$cs_version'",'
    echo -e '      "Crowdstrike RFM State": "'$cs_rfm_state'"'
    echo -e '    },'
    echo -e '    "Repositories": {'
    echo -e '      "Repositories List": "'$(apt-cache policy | grep "http" | awk '{print $2}' | sort -u | tr '\n' ',' | sed 's/,$//')'"'
    echo -e '    },'
    echo -e '    "Kernel Information": {'
    echo -e '      "Currently running kernel version": "'$(uname -r)'",'
    echo -e '      "Available Kernels": "'$(apt-cache policy linux-image-* | grep "Candidate" | awk '{print $2}' | sort -u | tr '\n' ',' | sed 's/,$//')'",'
    echo -e '      "Installed Kernel packages": "'$(dpkg -l linux-image-* | grep '^ii' | awk '{print $2}' | sed 's/-[0-9].*$//' | sort -u | tr '\n' ',' | sed 's/,$//')'"'
    echo -e '    }'
    echo -e '  }'
    echo -e "}"
  } > "$jsonReportFile"

  # Generate HTML report
  {
    echo -e "<pre>"
    echo -e " ##################################### "
    echo -e " Pre-Patch Report $(date) "
    echo -e " $HOSTNAME "
    echo -e
    echo -e "### PCM Services Checks ###"
    echo -e "BigFix agent: $(checkServiceStatus "BigFix BESClient" "BESClient")"
    echo -e "ScaleFT agent: $(checkServiceStatus "ScaleFT sftd" "sftd")"
    echo -e "Qualys agent: $(checkServiceStatus "Qualys qualys" "qualys")"
    echo -e "Splunk agent: $splunk_status"
    echo -e "    $splunk_last_checkin"
    echo -e "EnCase agent: $(checkServiceStatus "EnCase enlinux" "enlinux")"
    echo -e "Crowdstrike agent: $cs_status"
    echo -e "    Crowdstrike Version: $cs_version"
    echo -e "    Crowdstrike RFM State: $cs_rfm_state"
    echo -e "### End PCM Services Checks ###"
    echo -e
    echo -e "### Repositories ###"
    echo -e "Repositories"
    apt-cache policy | grep "http" | awk '{print $2}' | sort -u
    echo -e "### End Repositories###"
    echo -e
    echo -e "### Kernel Information ###"
    echo -e "Currently running kernel version is: $(uname -r)"
    echo -e
    echo -e "Available Kernels"
    apt-cache policy linux-image-* | grep "Candidate" | awk '{print $2}' | sort -u
    echo -e "Installed Kernel packages"
    dpkg -l linux-image-* | grep '^ii' | awk '{print $2}' | sed 's/-[0-9].*$//' | sort -u
    echo -e "### END Kernel Information ###"
    echo -e
    echo -e "### Drive Space Checks ###"
    echo -e "$regular_drive_space_check"
    echo -e
    echo -e "### END Pre-Patch Report ###"
    echo -e " ##################################### "
    echo -e "</pre>"
  } > "$htmlReportFile"

  # Encapsulate HTML report in code block
  sed -i '1s/^/[code]\n/' "$htmlReportFile"
  echo -e "[/code]" >> "$htmlReportFile"
}

checkDriveSpace
aptGetUpdate
checkSplunk
generatePrePatchReport
