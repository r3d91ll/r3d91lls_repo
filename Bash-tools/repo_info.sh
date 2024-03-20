#!/bin/bash

# Check for jq and install if it's not present
if ! command -v jq &> /dev/null; then
    echo "'jq' could not be found. Attempting to install..."
    # Try to install jq based on the package manager
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        case $ID in
            ubuntu|debian)
                sudo apt-get update && sudo apt-get install -y jq
                ;;
            rhel|centos|amzn)
                sudo yum install -y jq
                ;;
            *)
                echo "Could not install 'jq'. Please install it manually."
                exit 1
                ;;
        esac
    else
        echo "Unable to identify the package manager. Please install 'jq' manually."
        exit 1
    fi
fi

# Function to get repository info for YUM/DNF based systems
get_repo_info() {
    local cmd=$1  # 'yum' or 'dnf'
    while IFS= read -r repo_id _; do
        if ! repo_name=$($cmd repoinfo "$repo_id" | grep 'Repo-name' | sed 's/Repo-name\s*:\s*//'); then
            echo "Error fetching repository name for $repo_id"
            continue
        fi
        if ! repo_url=$($cmd repoinfo "$repo_id" | grep 'Repo-baseurl' | awk '{print $3}'); then
            echo "Error fetching repository URL for $repo_id"
            continue
        fi
        if [[ -n "$repo_url" ]]; then
            json+="{\"name\": \"$repo_name\", \"url\": \"$repo_url\"},"
        fi
    done < <($cmd repolist enabled | awk 'NR>1 {print $1 " " $0}')
}

# Function to get repository info for APT based systems
get_apt_repos() {
    if ! grep -h ^deb /etc/apt/sources.list /etc/apt/sources.list.d/* > /dev/null 2>&1; then
        echo "Error accessing APT sources list."
        return
    fi
    grep -h ^deb /etc/apt/sources.list /etc/apt/sources.list.d/* | \
    while IFS= read -r line; do
        repo_url=$(echo $line | cut -d' ' -f2)
        repo_name=$(echo $line | awk '{$1=$2=""; print $0}' | xargs)
        json+="{\"name\": \"$repo_name\", \"url\": \"$repo_url\"},"
    done
}

# Detect distribution and select package manager
if [ -f /etc/os-release ]; then
    . /etc/os-release
    case $ID in
        ubuntu|debian)
            pkg_manager="apt"
            ;;
        rhel|centos|amzn)
            if [[ $VERSION_ID =~ ^[7-9]$|^8$ ]]; then
                pkg_manager="dnf"
            else
                pkg_manager="yum"
            fi
            ;;
        *)
            echo "Unsupported distribution"
            exit 1
            ;;
    esac
else
    echo "/etc/os-release not found, cannot identify distribution."
    exit 1
fi

# Get hostname
hostname=$(hostname)

# Get primary IP address
primary_ip=$(hostname -I | awk '{print $1}')

# Initialize JSON
json="{\"hostname\": \"$hostname\", \"primary_ip\": \"$primary_ip\", \"repositories\": ["

# Fetch repository information based on the package manager
if [[ $pkg_manager == "apt" ]]; then
    get_apt_repos
else  # For yum or dnf
    get_repo_info $pkg_manager
fi

# Remove trailing comma
json=${json%,}

# Close JSON array and object
json+="]}"

# Output or save the JSON report
echo "$json" | jq '.' > report.json

# Check if jq succeeded and report is generated
if [ $? -eq 0 ]; then
    echo "Report generated successfully: report.json"
else
    echo "Error generating report."
fi
