#!/bin/bash

reportFile="reportFile.txt"  # Define the path to your report file.

# Function to append information to the report file.
append_report() {
    echo "$@" >> "$reportFile"
}

# Function to dynamically check disk space and extract LVM details.
check_disk_space() {
    local minSizeMB=$1
    local directory=$2
    local fsSource=$(df "$directory" --output=source | tail -n 1)
    local freeSpaceMB=$(df -BM "$directory" --output=avail | tail -n 1 | sed 's/M//')
    
    append_report "Checking disk space for $directory"
    append_report "Minimum required: ${minSizeMB}MB, Available: ${freeSpaceMB}MB."
    
    if [[ $freeSpaceMB -lt $minSizeMB ]]; then
        append_report "QC Fail: Insufficient disk space."
    else
        append_report "QC Pass: Sufficient disk space."
    fi

    # Check if the filesystem source is part of an LVM volume.
    if [[ $(lsblk -no TYPE "$fsSource" 2>/dev/null) == "lvm" ]]; then
        # Extract LV and VG names using lvdisplay.
        local lvName=$(lvdisplay "$fsSource" | grep -E "LV Name" | awk '{print $3}')
        local vgName=$(lvdisplay "$fsSource" | grep -E "VG Name" | awk '{print $3}')
        
        if [[ -n "$lvName" && -n "$vgName" ]]; then
            append_report "LVM volume detected. LV Name: $lvName, VG Name: $vgName"
            
            # Show free space in the VG.
            local vgFreeSpace=$(vgs --noheadings -o vg_free --units m "$vgName" | xargs)
            append_report "Free space in VG ($vgName): $vgFreeSpace"
        else
            append_report "Unable to extract LV and VG names for $directory."
        fi
    else
        append_report "$directory is not mounted on an LVM volume."
    fi

    append_report "10 largest files in the mount point:"
    find "$(df "$directory" --output=target | tail -n 1)" -xdev -type f -exec du -h {} + 2>/dev/null | sort -rh | head -n 10 >> "$reportFile"
}

# Call the function with the directory and minimum size required in MB.
check_disk_space 3000 "/var/cache/dnf"
