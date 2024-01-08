import os
import argparse
import subprocess
import json
import logging
import subprocess
from datetime import datetime, time
import sys
import re
import requests
import urllib.request
import csv

class CriticalSubprocessError(Exception):
    """Exception raised when a critical subprocess encounters an error."""
    pass

class PrePatchCheck:
    def __init__(self, changeNumber):
        try:
            self.initialize_variables(changeNumber)
            self.run_pre_patch_checks()
            self.setup_logging_and_output_paths()
            self.log_initial_state()
            self.generate_report()
            self.load_config()
            self.check_disk_space()
            self.log(f"Start time: {self.startTime}")
            self.log("Starting pre-patch check")
            self.log(f"Change number: {self.changeNumber}")
            self.log(f"Kernel versions: {self.kernelVersions}")
            self.log(f"Valid repositories: {self.validRepositories}")
            self.log(f"Package manager: {self.packageManager}")
            self.log(f"Output directory: {self.outputDirectory}")
            self.log(f"Debug log filepath: {self.debugLogFilepath}")
            self.log(f"Pre-patch report filepath: {self.prePatchReportFilepath}")
            self.log(f"CSV output: {self.csvOutput}")
            self.log(f"Instance ID: {self.get_instanceId()}")
            self.log(f"OS type: {self.identify_os()}")
            self.log(f"Kernel packages: {self.get_kernelPackages()}")
            self.log(f"Available kernels: {self.get_available_kernels()}")
            self.log(f"New kernel version: {self.get_newKernelVersion()}")
            self.log(f"CrowdStrike version: {self.get_crowdstrikeVersion()}")
            self.log(f"RFM state: {self.get_rfmState()}")
            self.log(f"Disk space: {self.check_disk_space()}")
            self.log(f"Manual intervention required: {self.manualInterventionRequired}")
            self.log(f"Failed functions: {self.failedFunctions}")
            self.log(f"End time: {datetime.now()}")
            self.log(f"Elapsed time: {datetime.now() - self.startTime}")
            self.log("Pre-patch check completed")
            self.stage_patch_script()
        except CriticalSubprocessError:
                self.update_critical_failure_report()
                sys.exit(1)


    def initialize_variables(self, changeNumber):
        self.changeNumber = changeNumber
        self.kernelVersions = {}
        self.validRepositories = []
        self.startTime = datetime.now()
        self.failedFunctions = []
        self.packageManager = 'dnf'
        self.manualInterventionNeeded = False
        self.outputDirectory = ""
        self.debugLogFilepath = ""
        self.prePatchReportFilepath = ""
        self.csvOutput = []
        self._instanceId = None
        self._newKernelVersion = None
        self._kernelPackages = None
        self._crowdstrikeVersion = None
        self._rfmState = None
        self.failedChecks = []
        self.manualInterventionRequired = False  # Add this line


    def log_initial_state(self):
        self.log(f"Start time: {self.startTime}")
        self.log("Starting pre-patch check")
        # ... (log other initial state information)
        self.log("Pre-patch check completed")

    def run_pre_patch_checks(self):
        self.log("Starting pre-patch checks...")

        # Load configurations
        if not self.load_config():
            self.log("Failed to load configurations. Exiting.")
            return False

        # Setup logging and output paths
        if not self.setup_logging_and_output_paths():
            self.log("Failed to set up logging and output paths. Exiting.")
            return False

        # Check disk space
        if not self.check_disk_space():
            self.log("Disk space check failed. Exiting.")
            return False

        # Identify OS type
        os_type = self.identify_os()
        if os_type == "Unknown":
            self.log("Failed to identify OS type. Exiting.")
            return False

        # Fetch instance ID
        instance_id = self.get_instanceId()
        if instance_id == "Unknown":
            self.log("Failed to fetch instance ID. Exiting.")
            return False

        # Fetch kernel packages
        kernel_packages = self.get_kernelPackages()
        if kernel_packages is None:
            self.log("Failed to fetch kernel packages. Exiting.")
            return False

        # Fetch available kernels
        available_kernels = self.get_available_kernels()
        if not available_kernels:
            self.log("Failed to fetch available kernels. Exiting.")
            return False

        # Fetch new kernel version
        new_kernel_version = self.get_newKernelVersion()
        if new_kernel_version is None:
            self.log("Failed to fetch new kernel version. Exiting.")
            return False

        # Fetch CrowdStrike version
        crowdstrike_version = self.get_crowdstrikeVersion()
        if crowdstrike_version in [
            "CrowdStrike not installed",
            "CrowdStrike error",
        ]:
            self.log("Failed to fetch CrowdStrike version. Exiting.")
            return False

        # Fetch RFM state
        rfm_state = self.get_rfmState()
        if rfm_state == "Error":
            self.log("Failed to fetch RFM state. Exiting.")
            return False

        self.log("Pre-patch checks completed successfully.")
        return True

    def load_config(self):
        self.log("Loading configurations...")  # Log method invocation
        url = "https://linux-kernels.s3-us-gov-west-1.amazonaws.com/linux-kernels.json"
        self.log(f"Fetching data from: {url}")  # Log the URL being accessed

        try:
            with urllib.request.urlopen(url) as response:
                config_data = response.read().decode()
        except urllib.error.URLError:
            self._extracted_from_load_config_10(
                "Failed to fetch configurations from the URL.",
                "Manual Intervention Required: Failed to download linux-kernels.json",
            )
            return
        except Exception as e:
            self.log(f"An unexpected error occurred while fetching the data: {e}")
            self.manualInterventionRequired = True
            return

        try:
            data = json.loads(config_data)
            self.kernelVersions = data.get('kernel_list', {})
            self.validRepositories = data.get('valid_repos', [])
        except ValueError:
            self._extracted_from_load_config_10(
                "Failed to parse the fetched configurations as JSON.",
                "Manual Intervention Required: JSON ERROR",
            )
        except Exception as e:
            self.log(f"An unexpected error occurred while parsing the JSON data: {e}")
            self.manualInterventionRequired = True

    # TODO Rename this here and in `load_config`
    def _extracted_from_load_config_10(self, arg0, arg1):
        self.log(arg0)
        self.update_prepatch_report(arg1)
        self.manualInterventionRequired = True

    def setup_logging_and_output_paths(self):
        self.outputDirectory = os.path.join("/root", self.changeNumber)
        self.debugLogFilepath = os.path.join(self.outputDirectory, "debug.log")
        self.prePatchReportFilepath = os.path.join(self.outputDirectory, "pre-patch.report")

        os.makedirs(self.outputDirectory, exist_ok=True)
        logging.basicConfig(filename=self.debugLogFilepath, level=logging.DEBUG)

    def log(self, message):
        """Log messages with a timestamp."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logging.debug(f"{timestamp}: {message}")

    def subprocess_output(self, cmd):
        self.log(f"Executing command: {' '.join(cmd)}")  # Log the command being issued
        try:
            result = subprocess.check_output(cmd, universal_newlines=True)
            output = result.strip()
            self.log(f"Command output: {output}")  # Log the command output
            return output
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed with return code: {e.returncode}. Error: {e.stderr}")
            raise CriticalSubprocessError("Command execution failed.") from e
        except Exception as e:
            self.log(f"Error executing command: {e}")
            raise CriticalSubprocessError(
                "Unexpected error during command execution."
            ) from e

    def update_critical_failure_report(self):
        with open(self.prePatchReportFilepath, 'w') as f:
            f.write("Critical Python Failure. Check logs for details.")

    def get_instanceId(self):
        if self._instanceId:
            return self._instanceId
        # Fetch instance id
        try:
            with urllib.request.urlopen("http://169.254.169.254/latest/meta-data/instance-id") as response:
                instance_id = response.read().decode()
        except urllib.error.URLError as e:
            self.log(f"Error fetching instance ID: {e}")
            self.manualInterventionRequired = True
            self.failedFunctions.append('get_instanceId')
            return "Unknown"
        else:
            self.log(f"Instance id: {instance_id}")
            return instance_id

    def identify_os(self):
        try:
            if os.path.isfile("/etc/redhat-release"):
                with open("/etc/redhat-release", "r") as file:
                    release_info = file.read()
                    self.osType = "Fedora" if "Fedora" in release_info else "RHEL/CentOS"
            elif os.path.isfile("/etc/system-release"):
                with open("/etc/system-release", "r") as file:
                    release_info = file.read()
                    if "Amazon Linux release 2" in release_info:
                        self.osType = "AWSLinux2"
                    elif "Amazon Linux release 2022" in release_info:  # Adjust this string if needed
                        self.osType = "AWSLinux2022"
                    else:
                        raise ValueError("Unexpected content in /etc/system-release.")
            else:
                raise IOError("OS identification files not found.")
        except (IOError, PermissionError) as e:
            self.log(f"Error reading OS identification file: {e}")
            self.osType = "Unknown"
        except ValueError as e:
            self.log(str(e))
            self.osType = "Unknown"
        except Exception as e:
            self.log(f"Unexpected error in identify_os: {e}")
            self.osType = "Unknown"
            self.manualInterventionRequired = True
            self.failedFunctions.append('identify_os')
        return self.osType

    def check_disk_space(self):
        try:
            stat = os.statvfs('/var')
            free_space_gb = (stat.f_frsize * stat.f_bavail) / (1024 * 1024 * 1024)
            self.csvOutput.append(f"{free_space_gb:.2f} GB")
            if free_space_gb < 2:
                self.failedChecks.append("Disk space less than 2GB")
                return False
            return True
        except OSError as e:
            return self._extracted_from_check_disk_space_11(
                'File system error when checking disk space: ', e
            )
        except Exception as e:
            return self._extracted_from_check_disk_space_11(
                'Unexpected error in check_disk_space: ', e
            )

    # TODO Rename this here and in `check_disk_space`
    def _extracted_from_check_disk_space_11(self, arg0, e):
        self.log(f"{arg0}{e}")
        self.failedChecks.append(f"Disk space check failed due to error: {e}")
        self.csvOutput.append("N/A")
        return False

    def validate_repos(self, os_version):
        try:
            result = subprocess.check_output(['yum', 'repo', 'list', 'enabled'], universal_newlines=True)
            enabled_repos = result.splitlines()
        except Exception as e:
            print(f"Error getting list of enabled repositories: {e}")
            return

        repo_names = [repo.split('/')[0] for repo in enabled_repos]
        repo_names = [repo for repo in repo_names if repo != '']
        repo_names = list(set(repo_names))

        print("Installed Repositories:")
        print(' '.join(repo_names))

    def get_newKernelVersion(self):
        if self._newKernelVersion:
            return self._newKernelVersion
        try:
            return self._extracted_from_get_newKernelVersion_5()
        except Exception as e:
            self._extracted_from_get_newKernelVersion_10(
                'Error in get_newKernelVersion: ',
                e,
                '. Please check the syntax of the linux-kernels.json file.',
            )

    #TODO Rename this here and in `get_newKernelVersion`
    def _extracted_from_get_newKernelVersion_5(self):
        os_version = self.osType
        desired_kernel_version = self.kernelVersions.get(os_version)
        if not self._available_kernels:
            self._available_kernels = self.get_available_kernels()
        if desired_kernel_version not in self._available_kernels:
            self._extracted_from_get_newKernelVersion_10(
                'Desired kernel version ',
                desired_kernel_version,
                ' not found in available kernels.',
            )
            return None  # or raise an exception
        self._newKernelVersion = desired_kernel_version
        return desired_kernel_version

    # TODO Rename this here and in `get_newKernelVersion`
    def _extracted_from_get_newKernelVersion_10(self, arg0, arg1, arg2):
        self.log(f"{arg0}{arg1}{arg2}")
        self.manualInterventionRequired = True
        self.failedFunctions.append('get_newKernelVersion')

    def get_available_kernels(self): 
        self.log("Fetching available kernels")
        try:
            result = subprocess.check_output([self.packageManager, "list", "available", "kernel*"], universal_newlines=True)
            available_kernels = result.strip().split('\n')
            self.log(f"Available kernels: {available_kernels}")
            return available_kernels
        except subprocess.CalledProcessError as e:
            self.log(f"Error fetching available kernels: {e.stderr}")
            return self._extracted_from_get_available_kernels_10(
                "Manual Intervention Required: Failed to fetch available kernels."
            )
        except Exception as e:
            self.log(f"Unexpected error fetching available kernels: {e}")
            return self._extracted_from_get_available_kernels_10(
                "Manual Intervention Required: Unexpected error while fetching available kernels."
            )

    # TODO Rename this here and in `get_available_kernels`
    def _extracted_from_get_available_kernels_10(self, arg0):
        self.update_prepatch_report(arg0)
        self.manualInterventionRequired = True
        return []

    def get_kernelPackages(self):
        if self._kernelPackages:
            return self._kernelPackages
        self.log("Fetching kernel packages for RHEL/CentOS, AWSLinux2, and AWSLinux2022")
        try:
            result = subprocess.check_output([self.packageManager, "list", "updates", "kernel*"], universal_newlines=True)
            kernel_packages = result.strip()
            if not kernel_packages:
                self.log("No kernel packages available for update.")
                return None
            self.log(f"Kernel packages: {kernel_packages}")
            return kernel_packages
        except subprocess.CalledProcessError as e:
            self.log(f"Error fetching kernel packages: {e.stderr}")
            return self._extracted_from_get_kernelPackages_15()
        except Exception as e:
            self.log(f"Unexpected error in get_kernelPackages: {e}")
            return self._extracted_from_get_kernelPackages_15()

    # TODO Rename this here and in `get_kernelPackages`
    def _extracted_from_get_kernelPackages_15(self):
        self.manualInterventionRequired = True
        self.failedFunctions.append('get_kernelPackages')
        return None

    def get_crowdstrikeVersion(self):
        self.log("Fetching CrowdStrike version")

        # Check if the CrowdStrike directory exists
        if not os.path.exists("/opt/CrowdStrike/"):
            self.log("CrowdStrike directory not found. Crowdstrike does not appear to be installed.")
            self.update_prepatch_report("Manual intervention - Crowdstrike does not appear to be installed")
            return "CrowdStrike not installed"

        try:
            return self._extracted_from_get_crowdstrikeVersion_11('CrowdStrike version: ')
        except subprocess.CalledProcessError as e:
            self.log(f"Error fetching CrowdStrike version. Error: {e.stderr}")
            self.log("Checking if the CrowdStrike service is running.")

            # Check if the CrowdStrike service is running
            service_status = subprocess.check_output(["systemctl", "status", "falcon-sensor"], universal_newlines=True)
            self.log(f"CrowdStrike service status: {service_status}")

            if "inactive" in service_status:
                self.log("CrowdStrike service is not running. Attempting to start it.")
                try:
                    subprocess.check_call(["systemctl", "start", "falcon-sensor"])
                    self.log("CrowdStrike service started successfully.")
                    time.sleep(2)  # Wait for 2 seconds before trying to fetch the version again
                except subprocess.CalledProcessError as e:
                    return self._extracted_from_get_crowdstrikeVersion_27(
                        'Failed to start CrowdStrike service. Error: ',
                        e,
                        "Manual remediation - Failed to start CrowdStrike service",
                    )
            # Try to fetch the CrowdStrike version again
            try:
                return self._extracted_from_get_crowdstrikeVersion_11(
                    'CrowdStrike version after service restart: '
                )
            except subprocess.CalledProcessError as e:
                return self._extracted_from_get_crowdstrikeVersion_27(
                    'Error fetching CrowdStrike version even after restarting the service. Error: ',
                    e,
                    "Manual remediation - Crowdstrike Error",
                )
        except Exception as e:
            self.log(f"Unexpected error in get_crowdstrikeVersion: {e}")
            self.update_prepatch_report("Manual remediation - Unexpected error in get_crowdstrikeVersion")
            return "CrowdStrike error"

    # TODO Rename this here and in `get_crowdstrikeVersion`
    def _extracted_from_get_crowdstrikeVersion_27(self, arg0, e, arg2):
        self.log(f"{arg0}{e.stderr}")
        self.update_prepatch_report(arg2)
        return "CrowdStrike error"

    # TODO Rename this here and in `get_crowdstrikeVersion`
    def _extracted_from_get_crowdstrikeVersion_11(self, arg0):
        result = subprocess.check_output(["/opt/CrowdStrike/falconctl", "-g", "--version"], universal_newlines=True)
        crowdstrike_version = result.strip()
        self.log(f"{arg0}{crowdstrike_version}")
        return crowdstrike_version

    def get_rfmState(self):
        if not self._crowdstrikeVersion:  # Check if CrowdStrike version was fetched successfully
            self.log("CrowdStrike version not found. Skipping RFM state check.")
            self.failedFunctions.append('get_rfmState')
            return "Unknown"

        self.log("Fetching RFM state")
        cmd = ["/opt/CrowdStrike/falconctl", "-g", "--rfm-state"]
        try:
            rfm_state = self.subprocess_output(cmd)
            self.log(f"RFM state: {rfm_state}")

            if rfm_state == "True":  # Check if RFM state is True
                self.log("RFM state is True. Kernel is out of alignment with Crowdstrike.")
                self.update_prepatch_report("Manual Remediation - Kernel out of alignment with Crowdstrike. RFM state True")
                self.manualInterventionRequired = True
                return "RFM True"
            return rfm_state
        except CriticalSubprocessError:
            self.log("Error fetching RFM state. Check if CrowdStrike is properly installed and running.")
            self.manualInterventionRequired = True
            self.failedFunctions.append('get_rfmState')
            return "Error"

    def dry_run_patch(self):
        self.log("Starting dry-run for kernel update")
        # Create the patchme.sh script with the --assumeno flag
        new_kernel_version = self.get_newKernelVersion()
        patchme_file = f"/root/{self.changeNumber}/patchme.sh"
        script_content = (
            "#!/bin/bash\n"
            f"newkernel=\"{new_kernel_version}\"\n"
            "yum --assumeno install $(while read p; do printf \"$p-$newkernel \"; done < /root/{self.changeNumber}/kernel_packages)\n"
            "yum --assumeno --security --exclude=kernel* update\n"
        )
        with open(patchme_file, 'w') as f:
            f.write(script_content)

        # Execute the patchme.sh script as a dry run
        try:
            subprocess.check_call(["bash", patchme_file])
            return True
        except Exception as e:
            self.log(f"Error in dry_run_patch: {e}")
            self.manualInterventionRequired = True
            self.failedFunctions.append('dry_run_patch')
            # Update PrePatchReport
            self.update_prepatch_report("Manual Intervention Required - Unknown Error")
            return False

    def stage_patch_script(self):
        patchme_file = f"/root/{self.changeNumber}/patchme.sh"
        temp_file = f"/root/{self.changeNumber}/temp.sh"
        with open(patchme_file, 'r') as src, open(temp_file, 'w') as dst:
            for line in src:
                dst.write(line.replace("--assumeno", "-y"))
        os.remove(patchme_file)
        os.rename(temp_file, patchme_file)
        # Make the patchme.sh file executable
        os.chmod(patchme_file, 0o744)
        # Update PrePatchReport
        self.update_prepatch_report("patchme.sh is executable")

    def generate_report(self):
        self.log("Generating report")

        # Determine the QC Pass status
        qc_pass_status = f"FAIL on {', '.join(self.failedFunctions)}" if self.manualInterventionRequired else "PASS"

        with open(self.prePatchReportFilepath, 'w', newline='') as f:
            writer = csv.writer(f)

            # Write the headers to the CSV file
            writer.writerow(["instance_id", "os_version", "NewKernelVersion", "available_kernels", "kernel_packages", "crowdstrike_version", "rfm_state", "/var_space_GB", "script_startTime", "script_end_time", "intervention_required", "QC Pass"])

            # Write the values to the CSV file
            writer.writerow([
                self.get_instanceId(), 
                self.identify_os(),
                self.get_newKernelVersion(),
                self.get_available_kernels(),
                self.get_kernelPackages(),
                self.get_crowdstrikeVersion(),
                self.get_rfmState(),
                self.csvOutput[-1],
                self.startTime,
                datetime.now(),
                "Manual Intervention Required" if self.manualInterventionNeeded else "No intervention required",
                qc_pass_status
            ])


        self.log("Report generated")


if __name__ == "__main__":
    changeNumber = os.environ.get('CHANGE_NUMBER')
    if not changeNumber:
        print("CHANGE_NUMBER environment variable not set.")
        sys.exit(1)
    check = PrePatchCheck(changeNumber)

    rfm_state = check.get_rfmState()
    if rfm_state == "RFM True":
        check.log("Skipping dry_run_patch due to RFM state being True.")

    elif check.dry_run_patch():
        check.stage_patch_script()
