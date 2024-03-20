#!/bin/bash

ChangeNumber=""
outputDir="/root/$ChangeNumber"
kernelPackageFile="/root/$ChangeNumber/kernel_packages"
reportFile="$outputDir/post-patch.report"
lvmPhysicalVolumes=()

append_report() {
    echo "$@" >> "$reportFile"
}

report_lvm_status() {
    local pvsOutput=$(pvs --noheadings -o pv_name 2>/dev/null)
    if [ -n "$pvsOutput" ]; then
        append_report "LVM Physical Volumes:"
        append_report "$pvsOutput"
        lvmPhysicalVolumes=($pvsOutput)
        append_report "LVM Volume Groups:"
        vgs >> "$reportFile"
        append_report "LVM Logical Volumes:"
        lvs >> "$reportFile"
    else
        append_report "LVM is not configured."
    fi
    append_report "--------------"
}

check_disk_space() {
    append_report "Disk Space Usage:"

    local rootFreeSpace=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$rootFreeSpace" -lt 10 ]; then
        append_report "QC Warning: Root partition has less than 10GB of free space. 5 largest files in root are listed below:"
        find / -xdev -type f -exec du -h {} + 2>/dev/null | sort -rh | head -n 5 >> "$reportFile"
    fi

    local cacheDir="/var/cache/"
    local cacheFreeSpace=$(df -BG "$cacheDir" | awk 'NR==2 {print $4}' | sed 's/G//')
    append_report "Disk Space Usage for /var/cache/ directory:"
    df -h "$cacheDir" | awk '!/^Filesystem/' >> "$reportFile"
    if [ "$cacheFreeSpace" -lt 3 ]; then
        append_report "QC Warning: /var/cache/ directory has less than 3GB of free space."
    else
        append_report "Sufficient space available in /var/cache/."
    fi

    append_report "--------------"

    if [ ${#lvmPhysicalVolumes[@]} -eq 0 ]; then
        df -h | awk '!/^tmpfs|^devtmpfs|^efivarfs/' >> "$reportFile"
    else
        for pv in "${lvmPhysicalVolumes[@]}"; do
            df -h | grep "$pv" >> "$reportFile"
        done
    fi

    append_report "--------------"
}

service_checks() {
    append_report "Service Status Checks:"
    append_report "--------------"

    local services=("falcon-sensor" "besclient" "sftd" "qualysd" "enlinuxd")

    append_report "CrowdStrike Status:"
    append_report "Current CrowdStrike version is: $(/opt/CrowdStrike/falconctl -g --version)"
    append_report "Current CrowdStrike RMF-Status is: $(/opt/CrowdStrike/falconctl -g --rfm-state)"

    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            append_report "Service $service is active:"
            systemctl status "$service" | awk 'NR>=3 && NR<=4' >> "$reportFile"
        else
            append_report "Service $service is not active or not found."
        fi
    done

    local splunkService=$(ps aux | grep '/opt/rackspace/splunkforwarder/bin' | grep -v grep | awk '{print $11 }' | sort -u)
    if [[ -n "$splunkService" ]]; then
        local serviceName=$(basename "$splunkService")
        append_report "Splunk Service Status:"
        append_report "Splunk Service '$serviceName' is active and running from /opt/rackspace/splunkforwarder/bin"
        systemctl status "$serviceName" | awk 'NR>=3 && NR<=4' >> "$reportFile"
    else
        append_report "QC Fail: Splunk service not found or not running from the expected directory"
    fi

    append_report "Services enabled at startup:"
    systemctl list-unit-files --state=enabled | egrep -i 'besclient|sftd|falcon|qualys|splunk|enlinux' >> "$reportFile"

    append_report "--------------"
}

list_recent_packages() {
    local packagesFile="$outputDir/patching-packages.list"
    local sinceTime=$(date --date='12 hours ago' '+%Y-%m-%d %H:%M')

    echo "Package List Since $sinceTime" > "$packagesFile"
    append_report "Transaction details for packages updated in the last 12 hours:"

    case $PAKMAN in
        dnf|yum)
            local transactionIds=$($PAKMAN history list | awk -v sinceTime="$sinceTime" '$0 >= sinceTime {print $1}')
            for transId in $transactionIds; do
                local transDetailFile="$outputDir/transaction-$transId-details.txt"
                append_report "Transaction ID: $transId"
                $PAKMAN history info --id="$transId" > "$transDetailFile"
                append_report "Details in: $transDetailFile"
                append_report "--------------"
            done
            ;;
        apt)
            local aptLogFile="/var/log/dpkg.log"
            local aptPackagesFile="$outputDir/apt-updated-packages.list"
            grep -E " install | upgrade " "$aptLogFile" | grep -E "$sinceTime" > "$aptPackagesFile"

            local totalAptPackages=$(wc -l < "$aptPackagesFile")
            append_report "Number of packages patched in the last 12 hours (APT): $totalAptPackages"
            append_report "Detailed list of APT patched packages is stored locally on the server in $aptPackagesFile"
            append_report "--------------"
            ;;
        *)
            rpm -qa --last | awk -v sinceTime="$sinceTime" '$0 >= sinceTime {print $0}' > "$packagesFile"
            local totalPackages=$(wc -l < "$packagesFile")
            append_report "Number of packages patched in the last 12 hours: $totalPackages"
            append_report "Detailed list of patched packages is stored locally on the server in $packagesFile"
            append_report "--------------"
            ;;
    esac

    local totalPackages=$(wc -l < "$packagesFile")
    append_report "Number of packages patched in the last 12 hours: $totalPackages"
    append_report "Detailed list of patched packages is stored locally on the server in $packagesFile"
    append_report "--------------"
}

generate_report() {
    append_report "Currently running kernel version is: $(uname -r)"
    append_report "--------------"
    append_report "Other Mounted Partitions:"
    df -h | awk '!/\/var\/cache\/'"$PAKMAN"'|'"$dir"'/' >> "$reportFile"
    append_report "--------------"
}

if command -v dnf &>/dev/null; then
    PAKMAN="dnf"
elif command -v yum &>/dev/null; then
    PAKMAN="yum"
elif command -v apt &>/dev/null; then
    PAKMAN="apt"
else
    echo "No supported package managers found."
    exit 1
fi

report_lvm_status
check_disk_space
service_checks
list_recent_packages
generate_report
cat "$reportFile"