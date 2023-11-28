#!/bin/bash

ChangeNumber="$1"
outputDir="/root/$ChangeNumber"
kernelPackageFile="$outputDir/kernel_packages"
reportFile="$outputDir/pre-patch.report"
min_free_space_gb=3

checkDriveSpace() {
  if [ -d "/var/cache/yum" ]; then
    df_out=$(df -Th /var/cache/yum/ | awk 'NR==2')
    available_space_gb=$(echo -e"$df_out" | awk '{print int($5)}')
    file_system=$(echo -e"$df_out" | awk '{print $2}')
    mount_point=$(echo -e"$df_out" | awk '{print $NF}')

    if [ "$available_space_gb" -ge "$min_free_space_gb" ]; then
      regular_drive_space_check="QC PASS: /var/cache/yum has ${available_space_gb}GB of free space."
    else
      regular_drive_space_check="QC FAIL: /var/cache/yum does not have enough free space for patching (${available_space_gb}G)."

      if [[ "$df_out" == *"/dev/mapper"* ]]; then
        lvm_drive_space_check=$(echo -e"$df_out" | awk -v file_system="$file_system" '{print "LVM is configured for /var/cache/yum and is using " file_system}')
        vg_name=$(pvs --noheadings -o vg_name --separator ' ' | awk '{print $1}')
        vg_free_space=$(vgs --noheadings -o vg_free --units g "$vg_name" --separator ' ')
        regular_drive_space_check+="\nVolume Group $vg_name has $vg_free_space free space."
        regular_drive_space_check+="\n$mount_point is using $file_system file system."
      else
        regular_drive_space_check+="\n$mount_point is not using LVM and uses $file_system file system."
      fi
    fi
  else
    regular_drive_space_check="this device does not use YUM. Please download the appropriate PrePatchChecks.sh file appropriate for this OS"
  fi
}


yumMakecache() {
  if [ "$available_space_gb" -ge "$min_free_space_gb" ]; then
    yum clean all -q
    rm -rf /var/cache/yum/*
    repoList=$(yum -v repolist | grep Repo-id | cut -d ":" -f2 | cut -d "/" -f1 || echo -e "Yum FAIL Make Cache\!")
    # yum makecache -q || echo -e "Yum FAIL Make Cache!"
  fi
}

checkServiceStatus() {
  local service_name="$1"
  local process_name="$2"
  local pid
  pid=$(pgrep "$process_name")
  if [ -n "$pid" ]; then
    echo -e "$service_name Running"
  else
    echo -e "$service_name NOT Running"
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
  splunk_status=$(/opt/rackspace/splunkforwarder/bin/splunk status | grep "splunkd is running")
  if [[ -n "$splunk_status" ]]; then
    splunk_last_checkin=$(grep "Connected to idx=" /opt/rackspace/splunkforwarder/var/log/splunk/splunkd.log | tail -n1 | awk '{split($0, a, " "); gsub("idx=|,", "", a[13]); print "Splunk connected to " a[13] " on " a[1] " at " a[2]}')
  else
    splunk_status="Splunk NOT Running"
    splunk_last_checkin="Splunk NOT Running"
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
    echo -e "$repolist"
    echo -e "### End Repositories###"
    echo -e
    echo -e "### Kernel Information ###"
    echo -e "Currently running kernel version is: $(uname -r)"
    echo -e
    echo -e "Available Kernels"
    yum list kernel --showduplicates | tail | awk '{ print $2 }'
    echo -e "Installed Kernel packages"
    yum list installed 'kernel*' | grep ^kernel | cut -d. -f1 | sort -u > /tmp/kernelPackageFile
    rpm -qa | egrep "^kernel" | sed 's/-[0-9].*$//'| sort -u >> /tmp/kernelPackageFile
    cat /tmp/kernelPackageFile | sort -u | tee $kernelPackageFile
    echo -e "### END Kernel Information ###"
    echo -e
    echo -e "### Drive Space Checks ###"
    echo -e "$regular_drive_space_check"
    echo -e
    echo -e "### END Pre-Patch Report ###"
    echo -e " ##################################### "

  } > "$reportFile"
  cat "$reportFile"
}

createJsonReport() {
  json_report_file="$outputDir/pre-patch.json"
  {
    echo -e "{"
    echo -e '  "Pre-Patch Report": {'
    echo -e '    "Timestamp": "'$(date)'",'
    echo -e '    "Hostname": "'$HOSTNAME'",'
    echo -e '    "PCM Services Checks": {'
    echo -e '      "BigFix agent": "'$(checkServiceStatus "BigFix BESClient" "BESClient")'",'
    echo -e '      "ScaleFT agent": "'$(checkServiceStatus "ScaleFT sftd" "sftd")'",'
    echo -e '      "Qualys agent": "'$(checkServiceStatus "Qualys qualys" "qualys")'",'
    echo -e '      "Splunk agent": "'$splunk_status'",'
    echo -e '      "Splunk Last Checkin": "'$last_checkin'",'
    echo -e '      "EnCase agent": "'$(checkServiceStatus "EnCase enlinux" "enlinux")'",'
    echo -e '      "Crowdstrike agent": "'$cs_status'",'
    echo -e '      "Crowdstrike Version": "'$cs_version'",'
    echo -e '      "Crowdstrike RFM State": "'$cs_rfm_state'"'
    echo -e '    },'
    echo -e '    "Repositories": {'
    echo -e '      "Repositories List": "'$(yum -v repolist | grep Repo-id | cut -d ":" -f2 | tr '\n' ',' | sed 's/,$//')'"'
    echo -e '    },'
    echo -e '    "Kernel Information": {'
    echo -e '      "Currently running kernel version": "'$(uname -r)'",'
    echo -e '      "Available Kernels": "'$(yum list kernel --showduplicates | tail | awk '{ print $2 }' | sed 's/,$//')'",'""
    echo -e '      "Installed Kernel packages": "'$(yum list installed 'kernel*' | grep ^kernel | cut -d. -f1 | sort -u | tr '\n' ',' | sed 's/,$//')'"'
    echo -e '    }'
    echo -e '  }'
    echo -e "}"
  } > "$json_report_file"
}

checkDriveSpace
yumMakecache
checkSplunk
checkCrowdstrike
generatePrePatchReport
createJsonReport
