#!/bin/bash

# Define the S3 bucket URL placeholder
S3_BUCKET_URL="https://your-s3-bucket-url"

# Identify the distribution and version
DISTRO_VERSION=$(cat /etc/*release)
DISTRO=$(echo "$DISTRO_VERSION" | grep -oP '(?<=^ID=).+' | tr -d '"')
VERSION=$(echo "$DISTRO_VERSION" | grep -oP '(?<=^VERSION_ID=).+' | tr -d '"')

# Convert the distro and version to lowercase (for consistency in naming)
DISTRO=$(echo "$DISTRO" | tr '[:upper:]' '[:lower:]')
VERSION=$(echo "$VERSION" | tr '[:upper:]' '[:lower:]')

# Based on distro and version, download the appropriate Python script
case "$DISTRO" in
    "rhel")
        case "$VERSION" in
            "9"|"8")
                wget "$S3_BUCKET_URL/LinuxPrePatchRHEL-Py3.py" -O patching_script.py
                ;;
            "7")
                wget "$S3_BUCKET_URL/LinuxPrePatchRHEL-Py27.py" -O patching_script.py
                ;;
            *)
                echo "Unsupported Linux Distro: $DISTRO $VERSION"
                exit 1
                ;;
        esac
        ;;
    "ubuntu")
        if [[ "$VERSION" == "18.04" || "$VERSION" > "18.04" ]]; then
            if python3 -c 'import sys; exit(sys.version_info < (3, 6))'; then
                wget "$S3_BUCKET_URL/LinuxPrePatchUbuntu.Py3.py" -O patching_script.py
            else
                echo "Unsupported Python version for Ubuntu"
                exit 1
            fi
        else
            echo "Unsupported Ubuntu version"
            exit 1
        fi
        ;;
    "aws1")
        if python -c 'import sys; exit(sys.version_info < (2, 7))'; then
            wget "$S3_BUCKET_URL/LinuxPrePatchAWS1-Py26.py" -O patching_script.py
        else
            echo "Unsupported Python version for AWS1"
            exit 1
        fi
        ;;
    *)
        echo "Unsupported Linux Distro: $DISTRO $VERSION"
        exit 1
        ;;
esac

# Ensure the downloaded script has execute permissions
chmod +x patching_script.py
