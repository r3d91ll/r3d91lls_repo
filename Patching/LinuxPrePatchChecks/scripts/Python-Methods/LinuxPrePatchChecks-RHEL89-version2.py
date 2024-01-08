import os
import argparse
import subprocess
import json
import logging
import subprocess
from datetime import datetime
import sys
import re

class CriticalSubprocessError(Exception):
    pass

class PrePatchCheck:
    def __init__(self, changeNumber):
        try:
            self.initialize_variables(changeNumber)
            self.run_pre_patch_checks()
            self.log_initial_state()
            self.generate_report()
            self.load_config()
            self.setup_logging_and_output_paths()
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
        if crowdstrike_version == "CrowdStrike not installed" or crowdstrike_version == "CrowdStrike error":
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
        cmd = [
            "curl",
            "https://linux-kernels.s3-us-gov-west-1.amazonaws.com/linux-kernels.json"
        ]
        self.log(f"Executing command: {' '.join(cmd)}")  # Log the command being issued
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            config_data = result.stdout
        except subprocess.CalledProcessError:
            self.log("Failed to fetch configurations from the URL.")
            self.update_prepatch_report("Manual Intervention Required: Failed to download linux-kernels.json")
            self.manualInterventionRequired = True
            return
        except Exception as e:
            self.log(f"An unexpected error occurred while executing the command: {e}")
            self.manualInterventionRequired = True
            return

        try:
            data = json.loads(config_data)
            self.kernelVersions = data.get('kernel_list', {})
            self.validRepositories = data.get('valid_repos', [])
        except json.JSONDecodeError:
            self.log("Failed to parse the fetched configurations as JSON.")
            self.update_prepatch_report("Manual Intervention Required: JSON ERROR")
            self.manualInterventionRequired = True
        except Exception as e:
            self.log(f"An unexpected error occurred while parsing the JSON data: {e}")
            self.manualInterventionRequired = True

    def setup_logging_and_output_paths(self):
        self.outputDirectory = os.path.join("/root", self.changeNumber)
        self.debugLogFilepath = os.path.join(self.outputDirectory, "debug.log")
        self.prePatchReportFilepath = os.path.join(self.outputDirectory, "pre-patch.report")
        
        os.makedirs(self.outputDirectory, exist_ok=True)
        logging.basicConfig(filename=self.debugLogFilepath, level=logging.DEBUG)
        open(self.debugLogFilepath, 'w').close()
        open(self.prePatchReportFilepath, 'w').close()

    def log(self, message):
        """Log messages with a timestamp."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logging.debug("{}: {}".format(timestamp, message))
    
    def subprocess_output(self, cmd):
        self.log(f"Executing command: {' '.join(cmd)}")  # Log the command being issued
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            output = result.stdout.strip()
            self.log(f"Command output: {output}")  # Log the command output
            return output
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed with return code: {e.returncode}. Error: {e.stderr}")
            raise CriticalSubprocessError("Command execution failed.")
        except Exception as e:
            self.log(f"Error executing command: {e}")
            raise CriticalSubprocessError("Unexpected error during command execution.")
    
    def update_critical_failure_report(self):
        with open(self.prePatchReportFilepath, 'w') as f:
            f.write("Critical Python Failure. Check logs for details.")

    def get_instanceId(self):
        if self._instanceId:
            return self._instanceId
        # Fetch instance id
        instance_id = self.subprocess_output(["curl", "-s", "http://169.254.169.254/latest/meta-data/instance-id"])
        if instance_id:
            self.log("Instance id: {}".format(instance_id))
            return instance_id
        else:
            self.log("Error fetching instance ID.")
            self.manualInterventionRequired = True
            self.failedFunctions.append('get_instanceId')
            return "Unknown"
    
    def identify_os(self):
        try:
            if os.path.isfile("/etc/redhat-release"):
                with open("/etc/redhat-release", "r") as file:
                    release_info = file.read()
                    if "Fedora" in release_info:
                        self.osType = "Fedora"
                    else:
                        self.osType = "RHEL/CentOS"
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
                raise FileNotFoundError("OS identification files not found.")
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
            self.log(f"File system error when checking disk space: {e}")
            self.failedChecks.append(f"Disk space check failed due to error: {e}")
            self.csvOutput.append("N/A")
            return False
        except Exception as e:
            self.log(f"Unexpected error in check_disk_space: {e}")
            self.failedChecks.append(f"Disk space check failed due to error: {e}")
            self.csvOutput.append("N/A")
            return False
    
    def validate_repos(os_version):
        # Load the linux-kernels.json file
        with open('linux-kernels.json', 'r') as file:
            data = json.load(file)
        
        # Get the list of valid repos for the detected OS version
        valid_repos = data['valid_repos'].get(os_version, [])
        non_valid_repos = data['non-valid_repos']

        # Get the list of enabled repositories
        try:
            result = subprocess.run(['yum', 'repo', 'list', 'enabled'], capture_output=True, text=True)
            enabled_repos = result.stdout.splitlines()
        except Exception as e:
            # Handle the exception if the command fails
            print(f"Error getting list of enabled repositories: {e}")
            return

        non_standard_repos = []
        disabled_repos = []

        # Check for non-valid repos and disable them
        for repo in non_valid_repos:
            if any(r.startswith(repo) for r in enabled_repos):
                try:
                    subprocess.run(['yum-config-manager', '--disable', f"{repo}*"], check=True)
                    print(f"Disabled non-valid repo: {repo}")
                    disabled_repos.append(repo)
                except Exception as e:
                    print(f"Error disabling non-valid repo {repo}: {e}")

        # Check for any other repos not in the valid list
        for repo in enabled_repos:
            if repo not in valid_repos and not any(r.startswith(repo) for r in non_valid_repos):
                non_standard_repos.append(repo)

        # Update the PrePatchReport based on the findings
        if non_standard_repos:
            print(f"Warning Non-Standard Repos enabled: {' '.join(non_standard_repos)}")
        elif not disabled_repos:
            print("PrePatchReport: Pass")
        else:
            print(f"PrePatchReport: Pass - Non Valid Repos disabled: {' '.join(disabled_repos)}")

    validate_repos('rhel_8')  # Example call

    def get_newKernelVersion(self):
        if self._newKernelVersion:
            return self._newKernelVersion
        try:
            os_version = self.osType
            desired_kernel_version = self.kernelVersions.get(os_version)
            available_kernels = self.get_available_kernels()
            if desired_kernel_version not in available_kernels:
                self.log(f"Desired kernel version {desired_kernel_version} not found in available kernels.")
                self.manualInterventionRequired = True
                self.failedFunctions.append('get_newKernelVersion')
                return None  # or raise an exception
            return desired_kernel_version
        except Exception as e:
            self.log(f"Error in get_newKernelVersion: {e}. Please check the syntax of the linux-kernels.json file.")
            self.manualInterventionRequired = True
            self.failedFunctions.append('get_newKernelVersion')
    
    def get_available_kernels(self):
        self.log("Fetching available kernels")
        try:
            result = subprocess.run([self.packageManager, "list", "available", "kernel*"], capture_output=True, text=True, check=True)
            available_kernels = result.stdout.strip().split('\n')
            self.log(f"Available kernels: {available_kernels}")
            return available_kernels
        except subprocess.CalledProcessError as e:
            self.log(f"Error fetching available kernels: {e.stderr}")
            self.update_prepatch_report("Manual Intervention Required: Failed to fetch available kernels.")
            self.manualInterventionRequired = True
            return []
        except Exception as e:
            self.log(f"Unexpected error fetching available kernels: {e}")
            self.update_prepatch_report("Manual Intervention Required: Unexpected error while fetching available kernels.")
            self.manualInterventionRequired = True
            return []
    
    def get_kernelPackages(self):
        if self._kernelPackages:
            return self._kernelPackages
        self.log("Fetching kernel packages for RHEL/CentOS, AWSLinux2, and AWSLinux2022")
        try:
            result = subprocess.run([self.packageManager, "list", "updates", "kernel*"], capture_output=True, text=True, check=True)
            kernel_packages = result.stdout.strip()
            if not kernel_packages:
                self.log("No kernel packages available for update.")
                return None
            self.log("Kernel packages: {}".format(kernel_packages))
            return kernel_packages
        except subprocess.CalledProcessError as e:
            self.log(f"Error fetching kernel packages: {e.stderr}")
            self.manualInterventionRequired = True
            self.failedFunctions.append('get_kernelPackages')
            return None
        except Exception as e:
            self.log(f"Unexpected error in get_kernelPackages: {e}")
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
            result = subprocess.run(["/opt/CrowdStrike/falconctl", "-g", "--version"], capture_output=True, text=True, check=True)
            crowdstrike_version = result.stdout.strip()
            self.log("CrowdStrike version: {}".format(crowdstrike_version))
            return crowdstrike_version
        except subprocess.CalledProcessError as e:
            self.log(f"Error fetching CrowdStrike version. Error: {e.stderr}")
            self.log("Checking if the CrowdStrike service is running.")

            # Check if the CrowdStrike service is running
            service_status = subprocess.run(["systemctl", "status", "falcon-sensor"], capture_output=True, text=True)
            self.log(f"CrowdStrike service status: {service_status.stdout}")

            if "inactive" in service_status.stdout:
                self.log("CrowdStrike service is not running. Attempting to start it.")
                try:
                    subprocess.run(["systemctl", "start", "falcon-sensor"], check=True)
                    self.log("CrowdStrike service started successfully.")
                    time.sleep(2)  # Wait for 2 seconds before trying to fetch the version again
                except subprocess.CalledProcessError as e:
                    self.log(f"Failed to start CrowdStrike service. Error: {e.stderr}")
                    self.update_prepatch_report("Manual remediation - Failed to start CrowdStrike service")
                    return "CrowdStrike error"

            # Try to fetch the CrowdStrike version again
            try:
                result = subprocess.run(["/opt/CrowdStrike/falconctl", "-g", "--version"], capture_output=True, text=True, check=True)
                crowdstrike_version = result.stdout.strip()
                self.log("CrowdStrike version after service restart: {}".format(crowdstrike_version))
                return crowdstrike_version
            except subprocess.CalledProcessError as e:
                self.log("Error fetching CrowdStrike version even after restarting the service. Error: {}".format(e.stderr))
                self.update_prepatch_report("Manual remediation - Crowdstrike Error")
                return "CrowdStrike error"

        except Exception as e:
            self.log(f"Unexpected error in get_crowdstrikeVersion: {e}")
            self.update_prepatch_report("Manual remediation - Unexpected error in get_crowdstrikeVersion")
            return "CrowdStrike error"
                        
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
        with open(patchme_file, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write(f"newkernel=\"{new_kernel_version}\"\n")
            f.write("yum --assumeno install $(while read p; do printf \"$p-$newkernel \"; done < /root/{self.changeNumber}/kernel_packages)\n")
            f.write("yum --assumeno --security --exclude=kernel* update\n")

        # Execute the patchme.sh script as a dry run
        try:
            result = subprocess.run(["bash", patchme_file])
            if result.returncode != 0:
                self.log("Dry-run failed")
                self.manualInterventionRequired = True
                self.failedFunctions.append('dry_run_patch')
                # Update PrePatchReport
                self.update_prepatch_report("Manual Intervention Required - Dry Run Fail")
                return False
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
        with open(patchme_file, 'r') as f:
            content = f.read().replace("--assumeno", "-y")
        with open(patchme_file, 'w') as f:
            f.write(content)
        # Make the patchme.sh file executable
        os.chmod(patchme_file, 0o755)
        # Update PrePatchReport
        self.update_prepatch_report("patchme.sh is executable")
    
    def generate_report(self):
        self.log("Generating report")
        
        # Determine the QC Pass status
        qc_pass_status = "PASS" if not self.manualInterventionRequired else f"FAIL on {', '.join(self.failedFunctions)}"
        
        with open(self.prePatchReportFilepath, 'w') as f:
            # Write the headers to the CSV file
            f.write("instance_id,os_version,NewKernelVersion,available_kernels,kernel_packages,crowdstrike_version,rfm_state,/var_space_GB,script_startTime,script_end_time,intervention_required,QC Pass\n")
            
            # Write the values to the CSV file
            f.write("{},{},{},{},{},{},{},{},{},{},{},{}".format(
                self.get_instanceId(), 
                self.identify_os(),  # Updated this line
                self.get_newKernelVersion(),
                self.get_available_kernels(),
                self.get_kernelPackages(),
                self.get_crowdstrikeVersion(),
                self.get_rfmState(),
                self.csvOutput[-1],  # The last element should be the /var disk space
                self.startTime,
                datetime.now(),
                "Manual Intervention Required" if self.manualInterventionRequired else "No intervention required",
                qc_pass_status  # This is the QC Pass status
            ))
        self.log("Report generated")

if __name__ == "__main__":
    changeNumber = os.environ.get('CHANGE_NUMBER')
    if not changeNumber:
        print("CHANGE_NUMBER environment variable not set.")
        sys.exit(1)
    check = PrePatchCheck(changeNumber)
    
    rfm_state = check.get_rfmState()
    if rfm_state != "RFM True":
        if check.dry_run_patch():
            check.stage_patch_script()
    else:
        check.log("Skipping dry_run_patch due to RFM state being True.")
