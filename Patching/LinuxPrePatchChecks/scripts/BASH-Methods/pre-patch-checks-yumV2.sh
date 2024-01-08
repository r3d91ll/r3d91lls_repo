#!/bin/bash

ChangeNumber="CHG0123TEST"
outputDir="/root/$ChangeNumber"
kernelPackageFile="$outputDir/kernel_packages"
reportFile="$outputDir/pre-patch.report"
min_free_space_gb=3

is_lvm_used() {
  [[ -L "$1" && "$(readlink -f "$1")" == "/dev/mapper/"* ]]
}

check_drive_space() {
  if [ -d "/var/cache/yum" ]; then
    available_space_gb=$(df -BG /var/cache/yum | awk 'NR==2 {print $4+0}')
    lvm_drive_space_check=$(is_lvm_used "/var/cache/yum" && echo "LVM is not configured for /var/cache/yum" || echo "")
    regular_drive_space_check=$([ "$available_space_gb" -ge "$min_free_space_gb" ] && echo "/var/cache/yum has at least ${min_free_space_gb}GB of free space" || echo "/var/cache/yum does not have enough free space (${available_space_gb}GB)")
  else
    regular_drive_space_check="/var/cache/yum does not exist or is not a directory"
  fi
}

yumMakecache() {
  if [ "$available_space_gb" -ge "$min_free_space_gb" ]; then
    yum clean all -q
    rm -rf /var/cache/yum/*
    yum makecache -q || echo "Yum FAIL Make Cache!"
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
    cs_cs_rfm_state=$(/opt/CrowdStrike/falconctl -g --rfm-state 2>/dev/null)
  else
    cs_status="Crowdstrike NOT Running"
    cs_version="Crowdstrike NOT Running"
    cs_rfm_state="Crowdstrike NOT Running"
  fi
}

generate_pre_patch_report() {
  mkdir -p "$outputDir"
  {
    echo -e "\033[1m Pre-Patch Report $(date) \033[0m"
    echo -e "\033[1m $HOSTNAME \033[0m"
    echo
    echo -e "\033[1m### Repositories ###\033[0m"
    yum -v repolist | grep Repo-id | cut -d ":" -f2
    echo -e "\033[1m### End Repositories###\033[0m"
    echo
    echo -e "\033[1m### PCM Services Checks ###\033[0m"
    check_service_status "Crowdstrike" "falcon"
    check_service_status "BigFix" "BESClient"
    check_service_status "ScaleFT" "sftd"
    check_service_status "Qualys" "qualys"
    check_service_status "Splunk" "splunk"
    check_service_status "EnCase" "enlinux"
    echo "Crowdstrike agent: $cs_status"
    echo "    Crowdstrike Version: $cs_version"
    echo "    Crowdstrike RFM State: $cs_rfm_state"
    # ... (rest of the report generation code)
  } > "$reportFile"
  cat "$reportFile"
}

check_drive_space
yumMakecache
check_crowdstrike
generate_pre_patch_report
