import os
import csv
import json
import logging
import subprocess
from datetime import datetime
import platform
import sys  # Importing sys to get command line arguments

class PrePatchCheck:

    def __init__(self, change_number):
        # Load input data from JSON from S3
        os.system("curl -o input.json https://linux-kernels.s3-us-gov-west-1.amazonaws.com/linux-kernels.json")

        with open('input.json', 'r') as file:
            data = json.load(file)

        self.change_number = change_number
        self.output_directory = os.path.join("/root", self.change_number)
        self.kernel_packages_filepath = os.path.join(self.output_directory, "kernel_packages_" + self.change_number)
        self.pre_patch_report_filepath = os.path.join(self.output_directory, "pre-patch.report")
        self.debug_log_filepath = os.path.join(self.output_directory, "debug.log")
        self.failed_checks = []  # list to store names of failed checks
        self.csv_output = []  # list to store the CSV output columns
        
        # Ensure previous logs and reports are overwritten
        open(self.debug_log_filepath, 'w').close()
        open(self.pre_patch_report_filepath, 'w').close()

        self.start_time = datetime.now()
        self.kernel_versions = data.get('kernel_list', {})
        self.failed_functions = []

        self._instance_id = None
        self._os_version = None
        self._new_kernel_version = None
        self._available_kernels = None
        self._kernel_packages = None
        self._crowdstrike_version = None
        self._rfm_state = None

        # Set up logging
        logging.basicConfig(filename=self.debug_log_filepath, level=logging.DEBUG)

        # Create output directory
        os.makedirs(self.output_directory, exist_ok=True)
        self.valid_repositories = data.get('valid_repos', [])

        # Identify OS and package manager
        self.identify_os_and_package_manager()
        self.manual_intervention_needed = False

    def load_config(self):
        """Load configurations from JSON."""
        try:
            os.system("curl -o input.json https://linux-kernels.s3-us-gov-west-1.amazonaws.com/linux-kernels.json")
            with open('input.json', 'r') as file:
                data = json.load(file)
            self.kernel_versions = data.get('kernel_list', {})
            self.valid_repositories = data.get('valid_repos', [])
        except Exception as e:
            logging.error(f"Failed to load configurations: {e}")
            sys.exit(1)
    
    def setup_logging_and_output_paths(self):
        """Setup logging and output paths."""
        self.output_directory = os.path.join("/root", self.change_number)
        self.debug_log_filepath = os.path.join(self.output_directory, "debug.log")
        self.pre_patch_report_filepath = os.path.join(self.output_directory, "pre-patch.report")
        os.makedirs(self.output_directory, exist_ok=True)

        logging.basicConfig(filename=self.debug_log_filepath, level=logging.DEBUG)
        open(self.debug_log_filepath, 'w').close()
        open(self.pre_patch_report_filepath, 'w').close()

    def check_disk_space(self):
        try:
            stat = os.statvfs('/var')
            free_space_gb = (stat.f_frsize * stat.f_bavail) / (1024 * 1024 * 1024)
            self.csv_output.append(f"{free_space_gb:.2f} GB")
            if free_space_gb < 2:
                self.failed_checks.append("Disk space less than 2GB")
                return False
            return True
        except Exception as e:
            self.failed_checks.append(f"Disk space check failed due to error: {e}")
            self.csv_output.append("N/A")
            return False

    # Consolidated function for OS and package manager identification
    def identify_os_and_package_manager(self):
        # Default to unknowns
        self.os_type = "Unknown"
        self.package_manager = "Unknown"
        
        if "Ubuntu" in platform.platform():
            self.os_type = "Ubuntu"
            # Check for apt binaries
            if os.path.exists('/usr/bin/apt'):
                self.package_manager = 'apt'
            elif os.path.exists('/usr/bin/apt-get'):
                self.package_manager = 'apt-get'
        elif os.path.isfile("/etc/redhat-release"):
            with open("/etc/redhat-release", "r") as file:
                release_info = file.read()
                if "Fedora" in release_info:
                    self.os_type = "Fedora"
                else:
                    self.os_type = "RHEL/CentOS"
            if os.path.exists('/usr/bin/dnf'):
                self.package_manager = 'dnf'
            elif os.path.exists('/usr/bin/yum'):
                self.package_manager = 'yum'

        if self.package_manager == "Unknown":
            self.log("Error: Package manager not identified")
            self.manual_intervention_required = True
            self.failed_functions.append('identify_os_and_package_manager')
        if self.os_type == "Unknown":
            self.log("Error: OS not identified")
            self.manual_intervention_required = True
            self.failed_functions.append('identify_os_and_package_manager')
        
    def log(self, message):
        """Log messages with a timestamp."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logging.debug("{}: {}".format(timestamp, message))
    
    def subprocess_output(self, cmd):
        try:
            output = subprocess.check_output(cmd, shell=isinstance(cmd, str))
            if isinstance(output, bytes):
                return output.decode('utf-8').strip()
            return output.strip()
        except subprocess.CalledProcessError:
            return None

    def create_patch_script(self):
        if not self.dry_run_patch():
            self.log("Skipping patch script creation due to failed dry-run")
            return

        self.log("Creating patchme.sh script")
        patchme_file = f"/root/{self.change_number}/patchme.sh"
        with open(patchme_file, 'w') as f:
            f.write("#!/bin/bash\n")
            new_kernel_version = self.get_new_kernel_version()
            patch_cmds = {
                "apt": f"apt-get install -y {new_kernel_version}",
                "dnf": f"dnf install -y {new_kernel_version}",
                "yum": f"yum -y install {new_kernel_version}"
            }
            f.write(patch_cmds.get(self.package_manager, "echo 'Unknown OS'"))

    def get_instance_id(self):
        if self._instance_id:
            return self._instance_id
        # Fetch instance id
        instance_id = self.subprocess_output(["curl", "-s", "http://169.254.169.254/latest/meta-data/instance-id"])
        if instance_id:
            self.log("Instance id: {}".format(instance_id))
            return instance_id
        else:
            self.log("Error fetching instance ID.")
            self.manual_intervention_required = True
            self.failed_functions.append('get_instance_id')
            return "Unknown"
    
    def identify_os(self):
        if "Ubuntu" in platform.platform():
            return "Ubuntu"
        elif os.path.isfile("/etc/redhat-release"):
            with open("/etc/redhat-release", "r") as file:
                release_info = file.read()
                if "Fedora" in release_info:
                    return "Fedora"
                else:
                    return "RHEL/CentOS"
        # Add more conditions as needed
        else:
            self.log("Error: OS not identified.")
            self.manual_intervention_required = True
            self.failed_functions.append('identify_os')
            return "Unknown"
    
    def validate_repos(self):
        # Validate and adjust repositories
        if "Ubuntu" in platform.platform():
            current_repos = subprocess.check_output("grep '^deb ' /etc/apt/sources.list | awk '{print $2}'", shell=True).decode().splitlines()
            for repo in current_repos:
                if repo not in self.valid_repos.values():
                    subprocess.check_call(f"sed -i '/{repo}/ s/^deb /#deb /' /etc/apt/sources.list", shell=True)
                    self.log(f"Disabled repository: {repo}")
        else:  # For others using yum (or dnf)
            current_repos = subprocess.check_output("yum repolist | awk '{print $1}'", shell=True).decode().splitlines()
            for repo in current_repos:
                if repo not in self.valid_repos:
                    subprocess.check_call(f"yum-config-manager --disable {repo}", shell=True)
                    self.log(f"Disabled repository: {repo}")

    def get_new_kernel_version(self):
        if self._new_kernel_version:
            return self._new_kernel_version
        try:
            os_version = self.get_os_version()
            desired_kernel_version = self.kernel_versions.get(os_version)
            available_kernels = self.get_available_kernels()
            if desired_kernel_version not in available_kernels:
                self.log(f"Desired kernel version {desired_kernel_version} not found in available kernels.")
                self.manual_intervention_required = True
                self.failed_functions.append('get_new_kernel_version')
            return desired_kernel_version
        except Exception as e:
            self.log(f"Error in get_new_kernel_version: {e}. Please check the syntax of the input.json file.")
            self.manual_intervention_required = True
            self.failed_functions.append('get_new_kernel_version')
    
    def get_available_kernels(self):
        if self._available_kernels:
            return self._available_kernels

        self.log("Fetching the 5 latest available kernels")
        if self.os_type == "Ubuntu":
            # Fetching the available kernels, then sorting them, and taking the top 5
            available_kernels = subprocess.check_output("apt list --upgradeable 2>/dev/null | grep linux-image | sort -V | tail -5", shell=True).decode().strip().splitlines()
        else:
            # Fetching the 5 latest kernels for non-Ubuntu distributions
            available_kernels = subprocess.check_output(["yum", "list", "kernel", "--showduplicates"]).decode().strip().splitlines()[:5]
        self.log("Available kernels: {}".format(", ".join(available_kernels)))
        self._available_kernels = available_kernels
        self.log("Available kernels: {}".format(", ".join(available_kernels)))
        return available_kernels

    def get_kernel_packages(self):
        if self._kernel_packages:
            return self._kernel_packages
        self.log("Fetching kernel packages")
        if "Ubuntu" in platform.platform():
            kernel_packages = subprocess.check_output("apt list --upgradeable | grep linux-", shell=True).decode().strip()
        else:
            kernel_packages = subprocess.check_output(["yum", "list", "updates", "kernel*"]).decode().strip()
        self.log("Kernel packages: {}".format(kernel_packages))
        return kernel_packages

    def dry_run_patch(self):
        self.log("Starting dry-run for kernel update")
        try:
            new_kernel_version = self.get_new_kernel_version()
            dry_run_cmd = {
                "apt": f"apt-get install --simulate {new_kernel_version}",
                "dnf": f"dnf install --assumeno {new_kernel_version}",
                "yum": f"yum install --assumeno {new_kernel_version}"
            }.get(self.package_manager)
            subprocess.check_call(dry_run_cmd, shell=True)
            self.log("Dry-run successful")
            return True
        except subprocess.CalledProcessError:
            self.log("Dry-run failed")
            self.manual_intervention_required = True
            self.failed_functions.append('dry_run_patch')
            return False
    
    def get_crowdstrike_version(self):
        if self._crowdstrike_version:
            return self._crowdstrike_version
        self.log("Fetching CrowdStrike version")
        try:
            crowdstrike_version = subprocess.check_output(["/opt/CrowdStrike/falconctl", "-g", "--version"]).decode().strip()
            self.log("CrowdStrike version: {}".format(crowdstrike_version))
            return crowdstrike_version
        except subprocess.CalledProcessError:
            self.log("CrowdStrike not found.")
            return "CrowdStrike not found"
        
    def get_rfm_state(self):
        if self._rfm_state:
            return self._rfm_state
        self.log("Fetching RFM state")
        rfm_state = subprocess.check_output(["/opt/CrowdStrike/falconctl", "-g", "--rfm-state"]).decode().strip()
        self.log("RFM state: {}".format(rfm_state))
        return rfm_state

    def generate_report(self):
        self.log("Generating report")
        intervention_message = "Manual intervention required" if self.manual_intervention_required else "No intervention required"
        
        # Determine the QC Pass status
        qc_pass_status = "PASS" if not self.manual_intervention_required else f"FAIL on {', '.join(self.failed_functions)}"
        
        with open(self.pre_patch_report_filepath, 'w') as f:
            # Write the headers to the CSV file
            f.write("instance_id,os_version,NewKernelVersion,available_kernels,kernel_packages,crowdstrike_version,rfm_state,/var_space_GB,script_start_time,script_end_time,intervention_required,QC Pass\n")
            
            # Write the values to the CSV file
            f.write("{},{},{},{},{},{},{},{},{},{},{},{}".format(
                self.get_instance_id(), 
                self.get_os_version(),
                self.get_new_kernel_version(),
                self.get_available_kernels(),
                self.get_kernel_packages(),
                self.get_crowdstrike_version(),
                self.get_rfm_state(),
                self.csv_output[-1],  # The last element should be the /var disk space
                self.start_time,
                datetime.now(),
                intervention_message,
                qc_pass_status  # This is the QC Pass status
            ))
        self.log("Report generated")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script_name.py <change_number>")
        sys.exit(1)
    change_number = sys.argv[1]
    pre_patch_checker = PrePatchCheck(change_number)
    # Check for disk space and store the result
    disk_space_check = pre_patch_checker.check_disk_space()
    # Validate repos only if disk_space_check is True
    if disk_space_check:
        pre_patch_checker.validate_repos()
        pre_patch_checker.generate_report()
        pre_patch_checker.create_patch_script()
    else:
        # Here you might also want to log or print that manual intervention is needed due to disk space
        pre_patch_checker.log("Manual intervention needed due to insufficient disk space.")
        pre_patch_checker.generate_report()