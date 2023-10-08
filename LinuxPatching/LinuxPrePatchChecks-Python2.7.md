# LinuxPrePatchChecks-Python2.7

## Description

`LinuxPrePatchChecks-Python2.7.py` is a Python 2.7 script designed to perform pre-patch checks on legacy RHEL7 devices. The script conducts a series of validations, kernel version checks, and preparations to facilitate a smooth kernel update process. It generates a detailed report based on the checks and operations performed, providing insights into the state of the system and any required interventions.

## Workflow

1. **Configuration Loading**: Fetches kernel and repository configurations from a remote URL.
2. **Logging and Output Setup**: Establishes logging and output paths for storing debug logs and pre-patch reports.
3. **Disk Space Check**: Validates available disk space in the `/var` directory.
4. **Kernel Update Logic**: Determines the current, desired, and available kernel versions, deciding on the appropriate action (update, no action, or manual intervention).
5. **Patch Script Creation**: Generates a `patchme.sh` script to be used for kernel updates.
6. **Instance ID Retrieval**: Obtains the instance ID of the machine.
7. **OS Identification**: Identifies the OS type (Ubuntu, Fedora, RHEL/CentOS).
8. **Repository Validation**: Checks and disables any repositories not listed in the valid repositories.
9. **Kernel Version Checks**: Retrieves and compares current, desired, and available kernel versions.
10. **Kernel Packages Retrieval**: Fetches kernel packages that need to be updated.
11. **Dry Run Patch**: Conducts a dry run of the kernel update to validate its success.
12. **CrowdStrike Version and RFM State Retrieval**: Retrieves the version of CrowdStrike installed and the RFM state.
13. **Report Generation**: Produces a report detailing the actions taken, system state, and any required interventions.

## Usage

```bash
python LinuxPrePatchChecks-Python2.7.py
```

Note: Ensure that the script is executed with appropriate permissions and in an environment where it can perform system-level checks and operations.

## To-Do List

### 1. Argument Parsing Improvement
- Transition from using a global variable (`CHANGE_NUMBER`) to utilizing argument parsing for enhanced flexibility and usability.

### 2. Enhanced Error Handling
- Implement more robust error handling and recovery mechanisms to manage unexpected scenarios gracefully.

### 3. Logging Enhancements
- Enhance logging to provide more detailed and user-friendly logs, facilitating easier debugging and auditing.

### 4. Testing and Validation
- Conduct thorough testing in various scenarios to validate the script’s logic and ensure it behaves as expected.

### 5. Code Optimization
- Review and optimize the code for efficiency, particularly in areas involving system calls and data processing.

### 6. Security Review
- Conduct a security review to ensure that the script adheres to best practices, especially in areas involving system calls and data handling.

### 7. Documentation
- Enhance inline documentation and comments to provide clear insights into the logic and operations of the script.

### 8. Transition to Python 3
- Consider transitioning the script to Python 3, given that Python 2.7 has reached the end of its life.

### 9. User Interaction
- Implement user interaction for manual interventions, providing clear instructions and options to the user.

### 10. Automated Testing
- Develop a suite of automated tests to validate the functionality and logic of the script in various scenarios.

## Contributing

Contributions to enhance and optimize the script are welcome. Please ensure to test any changes thoroughly before submitting a pull request.

## License

Ensure to include licensing information as per your project's requirements.
