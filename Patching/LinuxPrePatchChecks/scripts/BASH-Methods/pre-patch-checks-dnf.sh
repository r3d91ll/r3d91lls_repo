#!/bin/bash

# Define the ChangeNumber variable
ChangeNumber="CHG0123TEST"

# Define the output directory and file paths
outputDir="/root/$ChangeNumber"
kernelPackageFile="$outputDir/kernel_packages"
reportFile="$outputDir/pre-patch.report"

# Define the minimum required free space in GB
min_free_space_gb=3

# Function to check if LVM is used for a given mount point
is_lvm_used() {
  local mount_point="$1"
  [[ -L "$mount_point" && "$(readlink -f "$mount_point")" == "/dev/mapper/"* ]]
}

# Function to check drive space in /var
check_drive_space() {
  if [ -d "/var/cache/dnf" ]; then
    available_space_gb=$(df -BG /var/cache/dnf | awk 'NR==2 {print $4+0}')

    if is_lvm_used "/var/cache/dnf"; then
      vg_name=$(df -P /var/cache/dnf | awk 'NR==2 {print $1}')
      vg_free_space_gb=$(vgdisplay "$vg_name" | awk '/Free/ {print $7+0}')
      echo "Available space in VG $vg_name: ${vg_free_space_gb}GB"
    else
      echo "LVM is not configured for /var/cache/dnf"
    fi

    if [ "$available_space_gb" -ge "$min_free_space_gb" ]; then
      echo "/var/cache/dnf has at least ${min_free_space_gb}GB of free space"
    else
      echo "/var/cache/dnf does not have enough free space (${available_space_gb}GB)"
    fi
  else
    echo "/var/cache/dnf does not exist or is not a directory"
  fi
}

# Function to generate the pre-patch report
generate_pre_patch_report() {
  mkdir -p "$outputDir"
  cd "$outputDir" || exit

  #dnf clean all -q
  #rm -rf /var/cache/dnf/*
  #dnf makecache -q

  {
    echo -e "\033[1m Pre-Patch Report $(date) \033[0m"
    echo -e "\033[1m $HOSTNAME \033[0m"
    echo
    echo -e "\033[1m### Repositories ###\033[0m"
    dnf -v repolist | grep Repo-id | cut -d ":" -f2
    echo -e "\033[1m### End Repositories###\033[0m"
    echo
    echo -e "\033[1m### CrowdStrike Status ###\033[0m"
    cs_version=$(/opt/CrowdStrike/falconctl -g --version 2>/dev/null)
    cs_rfm_state=$(/opt/CrowdStrike/falconctl -g --rfm-state 2>/dev/null)
    if [ -n "$cs_version" ]; then
        if [ "$cs_rfm_state" == "true" ]; then
            echo -e "\033[1;31mTRUE - Crowdstrike is in Reduced Functionality Mode. Check running kernel version against the Crowdstrike Supported Kernel Tool.\033[0m" >> "$reportFile"
        else
            echo -e "\033[1;32mFALSE\033[0m" >> "$reportFile"
        fi
    else
        echo -e "Current CrowdStrike version is: \033[1;31mCROWDSTRIKE IS NOT INSTALLED\033[0m"
    fi

    if [ -n "$cs_rfm_state" ]; then
        echo "Current CrowdStrike RMF-Status is: $cs_rfm_state"
    else
        echo -e "Current CrowdStrike RMF-Status is: \033[1;31mCROWDSTRIKE IS NOT INSTALLED\033[0m"
    fi
    echo -e "\033[1m### End CrowdStrike Status ###\033[0m"

    echo

    echo -e "\033[1m### Kernel Information ###\033[0m"
    echo "Currently running kernel version is: $(uname -r)"
    echo
    echo "Available Kernels"
    dnf list kernel --showduplicates | tail
    echo
    echo "Installed Kernel packages"
    dnf list installed 'kernel*' | grep ^kernel | cut -d. -f1 | sort -u > /tmp/kernelPackageFile
    rpm -qa | egrep "^kernel" | sed 's/-[0-9].*$//'| sort -u >> /tmp/kernelPackageFile
    cat /tmp/kernelPackageFile | sort -u | tee $kernelPackageFile
    echo -e "\033[1m### END Kernel Information ###\033[0m"
    echo
    echo -e "\033[1m### Drive Space Check \033[0m"
    check_drive_space
    df -h /var/cache/dnf | grep "^/dev"
    echo -e "\033[1m### END Drive Space Check###\033[0m"
    echo
    echo -e "\033[1m### END Pre-Patch Report ###\033[0m"
  } > "$reportFile"

  clear
  cat "$reportFile"
}
# Call the functions
generate_pre_patch_report