import os
import argparse
import json
import logging
import subprocess
from datetime import datetime
import platform
import sys
import urllib2  # Modified import for Python 2.7

CHANGE_NUMBER = "CHG012345"  # Global variable for the change number

class PrePatchCheck:
    def __init__(self, change_number):
        self.load_config()
        self.change_number = change_number
        self.setup_logging_and_output_paths()
        self.start_time = datetime.now()
        self.failed_functions = []
        self.manual_intervention_needed = False

    def load_config(self):
        try:
            response = urllib2.urlopen('https://linux-kernels.s3-us-gov-west-1.amazonaws.com/linux-kernels.json')  # Modified urllib2 usage
            data = json.load(response)
            self.kernel_versions = data.get('kernel_list', {})
            self.valid_repositories = data.get('valid_repos', [])
        except Exception as e:
            logging.error("Failed to load configurations: {}".format(e))  # Modified string formatting
            sys.exit(1)

    def setup_logging_and_output_paths(self):
        self.output_directory = os.path.join("/root", self.change_number)
        self.debug_log_filepath = os.path.join(self.output_directory, "debug.log")
        self.pre_patch_report_filepath = os.path.join(self.output_directory, "pre-patch.report")
        
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)
        logging.basicConfig(filename=self.debug_log_filepath, level=logging.DEBUG)
        open(self.debug_log_filepath, 'w').close()
        open(self.pre_patch_report_filepath, 'w').close()

    def check_disk_space(self):
        try:
            stat = os.statvfs('/var')
            free_space_gb = (stat.f_frsize * stat.f_bavail) / (1024 * 1024 * 1024)
            self.csv_output.append("{:.2f} GB".format(free_space_gb))
            if free_space_gb < 2.5:
                self.failed_checks.append("Disk space less than 2.5GB")
                return False
            return True
        except Exception as e:
            self.failed_checks.append("Disk space check failed due to error: {}".format(e))
            self.csv_output.append("N/A")
            return False

    def log(self, message):
        """Log messages with a timestamp."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logging.debug("{}: {}".format(timestamp, message))
    
    def subprocess_output(self, cmd):
        try:
            result = subprocess.check_output(cmd, shell=True)  # Modified subprocess usage
            output = result.strip()
            if output:
                return output
            return None
        except subprocess.CalledProcessError:
            return None
        
    def check_and_update_kernel(self):
        try:
            # 2. Check Current Kernel Version
            current_kernel = self.get_current_kernel_version()
            
            # 3. Identify OS Version
            os_version = self.get_os_version()
            
            # 4. Determine Desired Kernel Version
            desired_kernel = self.kernel_versions.get(os_version)
            
            # 5. Compare Kernel Versions and Decide Action
            if current_kernel == desired_kernel:
                self.log("Kernel is up-to-date. No update required.")
                self.report["kernel_update"] = "Not required"
            elif self.is_version_higher(current_kernel, desired_kernel):
                self.log("Current kernel is higher than desired. Manual intervention required.")
                self.report["kernel_update"] = "Manual intervention required for potential downgrade"
                self.manual_intervention_required = True
            else:
                self.log("Kernel update required. Writing patch script.")
                self.report["kernel_update"] = "Update required to version {}".format(desired_kernel)
                self.create_patch_script(desired_kernel)
        except Exception as e:
            self.log("Error in check_and_update_kernel: {}".format(e))
            self.report["kernel_update"] = "Error encountered. Check logs."
            self.manual_intervention_required = True

    def create_patch_script(self):
        self.log("Creating patchme.sh script")
        patchme_file = "/root/{}/patchme.sh".format(self.change_number)  # Modified string formatting
        with open(patchme_file, 'w') as f:
            f.write("#!/bin/bash\n")
            new_kernel_version = self.get_new_kernel_version()
            patch_cmds = "yum --assumeno install $(while read p; do printf \"{}-{} \"; done < /root/{}/kernel_packages)".format(p, new_kernel_version, self.change_number)  # Modified string formatting
            f.write(patch_cmds)

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
        if "Ubuntu" in platform.platform():
            current_repos = self.subprocess_output("grep '^deb ' /etc/apt/sources.list | awk '{print $2}'")
            for repo in current_repos:
                if repo not in self.valid_repos.values():
                    self.subprocess_output("sed -i '/{}/ s/^deb /#deb /' /etc/apt/sources.list".format(repo))
                    self.log("Disabled repository: {}".format(repo))
        else:
            current_repos = self.subprocess_output("yum repolist | awk '{print $1}'")
            for repo in current_repos:
                if repo not in self.valid_repos:
                    self.subprocess_output("yum-config-manager --disable {}".format(repo))
                    self.log("Disabled repository: {}".format(repo))
    
    def get_current_kernel_version(self):
        try:
            current_kernel = subprocess.check_output(["uname", "-r"]).strip()
            self.log("Current kernel version: {}".format(current_kernel))
            return current_kernel
        except subprocess.CalledProcessError as e:
            self.log("Error getting current kernel version: {}".format(e))
            self.manual_intervention_required = True
            self.failed_functions.append('get_current_kernel_version')
            return None

    def get_new_kernel_version(self):
        if self._new_kernel_version:
            return self._new_kernel_version
        try:
            os_version = self.get_os_version()
            desired_kernel_version = self.kernel_versions.get(os_version)
            available_kernels = self.get_available_kernels()
            if desired_kernel_version not in available_kernels:
                self.log("Desired kernel version {} not found in available kernels.".format(desired_kernel_version))
                self.manual_intervention_required = True
                self.failed_functions.append('get_new_kernel_version')
            return desired_kernel_version
        except Exception as e:
            self.log("Error in get_new_kernel_version: {}. Please check the syntax of the input.json file.".format(e))
            self.manual_intervention_required = True
            self.failed_functions.append('get_new_kernel_version')
    
    def get_available_kernels(self):
        if self._available_kernels:
            return self._available_kernels

        self.log("Fetching the 5 latest available kernels")
        if self.os_type == "Ubuntu":
            result = subprocess.run("apt list --upgradeable 2>/dev/null | grep linux-image | sort -V | tail -5", capture_output=True, text=True)
            available_kernels = result.stdout.strip().splitlines()
        else:
            result = subprocess.run(["yum", "list", "kernel", "--showduplicates"], capture_output=True, text=True)
            available_kernels = result.stdout.strip().splitlines()[:5]
        self.log("Available kernels: {}".format(", ".join(available_kernels)))
        self._available_kernels = available_kernels
        self.log("Available kernels: {}".format(", ".join(available_kernels)))
        return available_kernels

    def get_kernel_packages(self):
        try:
            # Constructing the command to fetch kernel packages
            cmd = "yum list updates 'kernel*' | grep ^kernel | cut -d. -f1"
            
            # Executing the command and capturing the output
            kernel_packages = subprocess.check_output(cmd, shell=True).decode().strip()
            
            # Writing the kernel packages to a file
            with open("/root/{}/kernel_packages".format(self.change_number), 'w') as f:
                f.write(kernel_packages)
            
            # Logging the kernel packages
            self.log("Kernel packages: {}".format(kernel_packages))
            
            # Returning the kernel packages
            return kernel_packages
        
        except subprocess.CalledProcessError as e:
            # Logging an error if the subprocess call fails
            self.log("Error fetching kernel packages: {}".format(e))
            self.manual_intervention_required = True
            self.failed_functions.append('get_kernel_packages')
            return None

    def dry_run_patch(self):
        self.log("Starting dry-run for kernel update")
        try:
            patchme_file = "/root/{}/patchme.sh".format(self.change_number)
            result = subprocess.run(patchme_file, shell=True)
            if result.returncode == 0:
                self.log("Dry-run successful")
                with open(patchme_file, "r") as f:
                    lines = f.readlines()
                with open(patchme_file, "w") as f:
                    for line in lines:
                        f.write(line.replace("--assumeno", "-y"))
                return True
        except subprocess.CalledProcessError as e:
            self.log("Error in dry_run_patch: {}".format(e))
        self.log("Dry-run failed")
        self.manual_intervention_required = True
        self.failed_functions.append('dry_run_patch')
        return False
    
    def get_crowdstrike_version(self):
        if self._crowdstrike_version:
            return self._crowdstrike_version
        self.log("Fetching CrowdStrike version")
        try:
            result = subprocess.run(["/opt/CrowdStrike/falconctl", "-g", "--version"], capture_output=True, text=True)
            crowdstrike_version = result.stdout.strip()
            self.log("CrowdStrike version: {}".format(crowdstrike_version))
            return crowdstrike_version
        except subprocess.CalledProcessError:
            self.log("CrowdStrike not found.")
            return "CrowdStrike not found"
        
    def get_rfm_state(self):
        if self._rfm_state:
            return self._rfm_state
        self.log("Fetching RFM state")
        result = subprocess.run(["/opt/CrowdStrike/falconctl", "-g", "--rfm-state"], capture_output=True, text=True)
        rfm_state = result.stdout.strip()
        self.log("RFM state: {}".format(rfm_state))
        return rfm_state

    def generate_report(self):
        self.end_time = datetime.now()
        self.log("Generating report")
        intervention_message = "Manual intervention required" if self.manual_intervention_required else "No intervention required"
        
        qc_pass_status = "PASS" if not self.manual_intervention_required else "FAIL on {}".format(', '.join(self.failed_functions))
        
        with open(self.pre_patch_report_filepath, 'w') as f:
            f.write("instance_id,os_version,NewKernelVersion,available_kernels,kernel_packages,crowdstrike_version,rfm_state,/var_space_GB,script_start_time,script_end_time,intervention_required,QC Pass\n")
            f.write("{},{},{},{},{},{},{},{},{},{},{},{}".format(
                self.get_instance_id(), 
                self.get_os_version(),
                self.get_new_kernel_version(),
                self.get_available_kernels(),
                self.get_kernel_packages(),
                self.get_crowdstrike_version(),
                self.get_rfm_state(),
                self.csv_output[-1],
                self.start_time,
                self.end_time,
                intervention_message,
                qc_pass_status
            ))
        self.log("Report generated")

    def check_change_number(change_number):
        if not change_number.isdigit():
            print("Change number should be a digit")
            sys.exit(1)
        elif int(change_number) < 0:
            print("Change number should be a positive integer")
            sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Copy files based on change number.')
    parser.add_argument('change_number', type=str, help='Change number')

    args = parser.parse_args()
    change_number = args.change_number
    check = PrePatchCheck(CHANGE_NUMBER)

    check.load_config()
    check.setup_logging_and_output_paths()
    check.check_disk_space()
    check.identify_os()
    check.create_patch_script()
    check.get_instance_id()
    check.get_new_kernel_version()
    check.get_available_kernels()
    check.get_kernel_packages()
    check.dry_run_patch()
    check.get_crowdstrike_version()
    check.get_rfm_state()
    check.generate_report()