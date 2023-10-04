#!/bin/bash

if command -v python2.7 >/dev/null 2>&1; then
    echo "Python 2.7 is available. Downloading and running Python 2.7 script..."
    wget -O LinuxPrePatchChecks-Python2.7.py "https://inc0361448.s3.us-gov-west-1.amazonaws.com/LinuxPrePatchChecks-Python2.7.py"
    python2.7 LinuxPrePatchChecks-Python2.7.py
elif command -v python3 >/dev/null 2>&1; then
    echo "Python 3 is available. Downloading and running Python 3 script..."
    wget -O LinuxPrePatchChecks-Python3.py "https://inc0361448.s3.us-gov-west-1.amazonaws.com/LinuxPrePatchChecks-Python3.py"
    python3 LinuxPrePatchChecks-Python3.py
else
    echo "No compatible Python version found on $HOSTNAME. Please manually check the Python version."
    exit 1
fi