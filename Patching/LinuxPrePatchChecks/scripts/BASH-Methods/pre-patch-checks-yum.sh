#!/bin/bash

ChangeNumber="$1"
outputDir="/root/$ChangeNumber"
kernelPackageFile="$outputDir/kernel_packages"
reportFile="$outputDir/pre-patch.report"
min_free_space_gb=3

check_drive_space() {
  if [ -d "/var/cache/yum" ]; then
    df_out=$(df -Th /var/cache/yum/ | grep "^/")
    available_space_gb=$(echo "$df_out" | awk '{gsub("G","",$5); print $5}')
    lvm_drive_space_check=$(echo "$df_out" | awk -v file_system="$file_system" '$1 ~ /^\/dev\/mapper/ {print "LVM is configured for /var/cache/yum and is using " file_system}')    regular_drive_space_check=$([ "${available_space_gb%.*}" -ge "$min_free_space_gb" ] && echo "/var/cache/yum has at least ${min_free_space_gb}GB of free space" || echo "/var/cache/yum does not have enough free space (${available_space_gb}G)")
    vg_name=$(echo "$df_out" | cut -d"/" -f4 | awk '{print $1}' | cut -d- -f1)
    vg_free_space=$(vgdisplay "$vg_name" | awk '/Free/ {print $7}')
    file_system=$(echo "$df_out" | cut -d"/" -f4 | awk '{print $2}')
  else
    regular_drive_space_check="/var/cache/yum does not exist or is not a directory"
  fi
}

yumMakecache() {
  if [ "$available_space_gb" -ge "$min_free_space_gb" ]; then
    yum clean all -q
    rm -rf /var/cache/yum/*
    repoList=$(yum -v repolist | grep Repo-id | cut -d ":" -f2 | cut -d "/" -f1 || echo "Yum FAIL Make Cache\!")
    # yum makecache -q || echo "Yum FAIL Make Cache!"
  fi
}

check_service_status() {
  local service_name="$1"
  local process_name="$2"
  local pid
  pid=$(pgrep "$process_name")
  if [ -n "$pid" ]; then
    echo "$service_name Running"
  else
    echo "$service_name NOT Running"
  fi
}

check_crowdstrike() {
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

check_splunk() {
  splunk_status=$(/opt/rackspace/splunkforwarder/bin/splunk status | grep "splunkd is running")
  if [[ -n "$splunk_status" ]]; then
    splunk_last_checkin=$(grep "Connected to idx=" /opt/rackspace/splunkforwarder/var/log/splunk/splunkd.log | tail -n1 | awk '{split($0, a, " "); gsub("idx=|,", "", a[13]); print "Splunk connected to " a[13] " on " a[1] " at " a[2]}')
  else
    splunk_status="Splunk NOT Running"
    splunk_last_checkin="Splunk NOT Running"
  fi
}

generate_pre_patch_report() {
  mkdir -p "$outputDir"
  {
    echo "##################################### "
    echo -e " Pre-Patch Report $(date) "
    echo -e " $HOSTNAME "
    echo
    echo -e "### PCM Services Checks ###"
    echo "BigFix agent: $(check_service_status "BigFix BESClient" "BESClient")"
    echo "ScaleFT agent: $(check_service_status "ScaleFT sftd" "sftd")"
    echo "Qualys agent: $(check_service_status "Qualys qualys" "qualys")"
    echo "Splunk agent: $splunk_status"
    echo "    $splunk_last_checkin"
    echo "EnCase agent: $(check_service_status "EnCase enlinux" "enlinux")"
    echo "Crowdstrike agent: $cs_status"
    echo "    Crowdstrike Version: $cs_version"
    echo "    Crowdstrike RFM State: $cs_rfm_state"
    echo -e "### End PCM Services Checks ###"
    echo
    echo -e "### Repositories ###"
    echo "$repolist"
    echo -e "### End Repositories###"
    echo
    echo -e "### Kernel Information ###"
    echo "Currently running kernel version is: $(uname -r)"
    echo
    echo "Available Kernels"
    yum list kernel --showduplicates | tail | awk '{ print $2 }'
    echo "Installed Kernel packages"
    yum list installed 'kernel*' | grep ^kernel | cut -d. -f1 | sort -u > /tmp/kernelPackageFile
    rpm -qa | egrep "^kernel" | sed 's/-[0-9].*$//'| sort -u >> /tmp/kernelPackageFile
    cat /tmp/kernelPackageFile | sort -u | tee $kernelPackageFile
    echo -e "### END Kernel Information ###"
    echo
    echo -e "### END Pre-Patch Report ###"
  } > "$reportFile"
  cat "$reportFile"
}

create_json_report() {
  json_report_file="$outputDir/pre-patch.json"
  {
    echo "{"
    echo '  "Pre-Patch Report": {'
    echo '    "Timestamp": "'$(date)'",'
    echo '    "Hostname": "'$HOSTNAME'",'
    echo '    "PCM Services Checks": {'
    echo '      "BigFix agent": "'$(check_service_status "BigFix BESClient" "BESClient")'",'
    echo '      "ScaleFT agent": "'$(check_service_status "ScaleFT sftd" "sftd")'",'
    echo '      "Qualys agent": "'$(check_service_status "Qualys qualys" "qualys")'",'
    echo '      "Splunk agent": "'$splunk_status'",'
    echo '      "Splunk Last Checkin": "'$last_checkin'",'
    echo '      "EnCase agent": "'$(check_service_status "EnCase enlinux" "enlinux")'",'
    echo '      "Crowdstrike agent": "'$cs_status'",'
    echo '      "Crowdstrike Version": "'$cs_version'",'
    echo '      "Crowdstrike RFM State": "'$cs_rfm_state'"'
    echo '    },'
    echo '    "Repositories": {'
    echo '      "Repositories List": "'$(yum -v repolist | grep Repo-id | cut -d ":" -f2 | tr '\n' ',' | sed 's/,$//')'"'
    echo '    },'
    echo '    "Kernel Information": {'
    echo '      "Currently running kernel version": "'$(uname -r)'",'
    echo '      "Available Kernels": "'$(yum list kernel --showduplicates | tail | awk '{ print $2 }' | sed 's/,$//')'",'""
    echo '      "Installed Kernel packages": "'$(yum list installed 'kernel*' | grep ^kernel | cut -d. -f1 | sort -u | tr '\n' ',' | sed 's/,$//')'"'
    echo '    }'
    echo '  }'
    echo "}"
  } > "$json_report_file"
}

check_drive_space
yumMakecache
check_splunk
check_crowdstrike
generate_pre_patch_report
create_json_report
