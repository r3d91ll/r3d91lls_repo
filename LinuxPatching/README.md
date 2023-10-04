```markdown
# Linux Patching Scripts

This repository contains scripts designed to facilitate Linux system patching by conducting pre-patch checks using various versions of Python and a shell script. The scripts gather various system metrics and configurations to audit the system status before applying patches.

## Scripts Overview

### 1. [LinuxPrePatchChecks-Python2.7.py](https://github.com/r3d91ll/r3d91lls_repo/blob/main/LinuxPatching/LinuxPrePatchChecks-Python2.7.py)
- **Language**: Python 2.7
- **Purpose**: Conducts pre-patch checks on a Linux system, gathering various system metrics and configurations.

### 2. [LinuxPrePatchChecks-Python3.py](https://github.com/r3d91ll/r3d91lls_repo/blob/main/LinuxPatching/LinuxPrePatchChecks-Python3.py)
- **Language**: Python 3
- **Purpose**: Similar to the Python 2.7 script, it performs pre-patch checks and is adapted for Python 3 environments.

### 3. [LinuxPrePatchChecks.sh](https://github.com/r3d91ll/r3d91lls_repo/blob/main/LinuxPatching/LinuxPrePatchChecks.sh)
- **Language**: Shell Script
- **Purpose**: Determines the version of Python running on a Linux instance and pulls the correct version of the Python pre-patch check script. Intended to become an SSM document.

### 4. [linux-kernels.json](https://github.com/r3d91ll/r3d91lls_repo/blob/main/LinuxPatching/linux-kernels.json)
- **Type**: JSON File
- **Purpose**: Stores data related to Linux kernels, possibly utilized by the Python scripts during checks.

## Workflow

1. **Python Scripts Testing**: The Python scripts (`LinuxPrePatchChecks-Python2.7.py` and `LinuxPrePatchChecks-Python3.py`) are currently under testing across various supported Linux distributions to ensure accurate and reliable pre-patch checks.

2. **Shell Script Integration**: Upon completion of Python scripts testing, the shell script (`LinuxPrePatchChecks.sh`) will be tested. This script is designed to:
   - Determine the version of Python running on an instance.
   - Pull and execute the appropriate version of the Python pre-patch check script.

3. **SSM Document Creation**: The shell script will eventually be transformed into an SSM document to facilitate automated patch management in AWS environments.

## Usage

### Python Scripts
Execute the relevant Python script according to the Python version available on your system:
```bash
python LinuxPrePatchChecks-Python2.7.py
```
or
```bash
python3 LinuxPrePatchChecks-Python3.py
```

### Shell Script
Execute the shell script using bash:
```bash
bash LinuxPrePatchChecks.sh
```

## Contributing
Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## License
This project is licensed under the MIT License - see the LICENSE.md file for details.

