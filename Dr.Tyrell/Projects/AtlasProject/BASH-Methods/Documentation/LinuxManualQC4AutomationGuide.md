# Manual Patching of Linux Devices

This document outlines the process for performing a manual QC for Linux patching on RHEL, AWSLinux, and Ubuntu devices by the PCM-Ops team. The procedure involves preparing a device for patching, generating a report, and updating a Ticket. The Ticket update will confirm that the Change has been QC'ed and provide the information on the Qualys job that will patch the device.

Please note that we are working to automate the QC process. However until that is deployed fully and implemented, I have created this manual QC process which is very similar to our Manual Linux patching process located here: https://github.rackspace.com/Texas-Dir-Operations/Ops-Tooling/blob/LinuxPrePatchChecks-Todd/PatchingScripts/LinuxPrePatchChecks/scripts/BASH-Methods/LinuxManualPatching.md

Pro-Tip: Copy the raw version of this document into a text editor and use find-and-replace for "{ChangeNumber}" to update all commands with the correct directory and change number. When you find the correct kernel, do another find-and-replace on the current value of the newkernel variable to update all relevant scripts and the Ticket Update.

## Creating the Pre-Patch Report

Update the ChangeNumber variable in the appropriate code below to match the change number you are working out of. Then, copy and paste the code into the CLI of the device you're preparing for patching.

AWSLinux1 AWSLinux2 RHEL7 and RHEL8 Version (AKA the YUM version)
```bash
sudo -i
ChangeNumber="{ChangeNumber}" 
outputDir="/root/$ChangeNumber" 
kernelPackageFile="/root/$ChangeNumber/kernel_packages" 
reportFile="$outputDir/pre-patch.report" 
rm -rf "$outputDir"
mkdir -p "$outputDir" 
cd "$outputDir" 
yum clean all 
rm -rf /var/cache/yum/* 
yum makecache -q 
echo "### Pre-Patch Report > "$reportFile" 
echo "### $HOSTNAME >> "$reportFile" 
echo "Repositories" >> "$reportFile" 
yum -v repolist | grep Repo-id | cut -d ":" -f2 >> "$reportFile" 
echo "END Repository List" >> "$reportFile" 
echo >> "$reportFile" 
echo "Available Kernels" >> "$reportFile" 
yum list kernel --showduplicates | tail >> "$reportFile" 
echo "Available Kernels End" >> "$reportFile" 
echo >> "$reportFile" 
echo "Currently running kernel version is: $(uname -r)" >> "$reportFile" 
echo >> "$reportFile" 
yum list installed 'kernel*' | grep ^kernel | cut -d. -f1 | sort -u > /tmp/kernelPackageFile
rpm -qa | egrep "^kernel" | sed 's/-[0-9].*$//'| sort -u >> /tmp/kernelPackageFile
cat /tmp/kernelPackageFile | sort -u > $kernelPackageFile
echo "Current CrowdStrike version is: $(/opt/CrowdStrike/falconctl -g --version)" >> "$reportFile" 
echo "Current CrowdStrike RMF-Status is: $(/opt/CrowdStrike/falconctl -g --rfm-state)" >> "$reportFile" 
echo >> "$reportFile" 
echo "Installed Kernel packages" >> "$reportFile" 
cat "$kernelPackageFile" >> "$reportFile" 
echo "Kernel packages installed end" >> "$reportFile" 
echo "Space Available for YUM: " >> "$reportFile" 
df -h /var >> "$reportFile" 
echo >> "$reportFile" 
clear
cat "$reportFile"
```

AWSLinux2 RHEL8 and RHEL9 Versions (AKA the DNF version)
```bash
sudo -i
ChangeNumber="{ChangeNumber}" 
outputDir="/root/$ChangeNumber" 
kernelPackageFile="/root/$ChangeNumber/kernel_packages" 
reportFile="$outputDir/pre-patch.report" 
rm -rf "$outputDir"
mkdir -p "$outputDir" 
cd "$outputDir" 
dnf clean all 
rm -rf /var/cache/dnf/* 
dnf makecache -q 
# Ensure that dnf-plugin-core is installed
dnf -y install dnf-plugins-core
echo "$HOSTNAME repolist" > "$reportFile" 
dnf -v repolist | grep Repo-id | cut -d ":" -f2 >> "$reportFile" 
echo "$HOSTNAME repolist end" >> "$reportFile" 
echo 
echo "Available Kernels" >> "$reportFile" 
dnf list kernel --showduplicates | tail >> "$reportFile" 
echo "Available Kernels End" >> "$reportFile" 
echo 
echo "Currently running kernel version is: $(uname -r)" >> "$reportFile" 
echo 
dnf list installed 'kernel*' | grep ^kernel | cut -d. -f1 | sort -u > "$kernelPackageFile"
echo "Current CrowdStrike version is: $(/opt/CrowdStrike/falconctl -g --version)" >> "$reportFile" 
echo "Current CrowdStrike RMF-Status is: $(/opt/CrowdStrike/falconctl -g --rfm-state)" >> "$reportFile" 
echo 
echo "Kernel packages installed" >> "$reportFile" 
cat "$kernelPackageFile" >> "$reportFile" 
echo "Kernel packages installed end" >> "$reportFile" 
echo "Drive space: " >> "$reportFile" 
df -h /var >> "$reportFile" 
clear
cat "$reportFile"
```

Ubuntu and Debian Version (AKA the APT version)
```bash
sudo -i
ChangeNumber="{ChangeNumber}" 
outputDir="/root/$ChangeNumber" 
kernelPackageFile="/root/$ChangeNumber/kernel_packages" 
reportFile="$outputDir/pre-patch.report" 
rm -rf "$outputDir"
mkdir -p "$outputDir" 
cd "$outputDir" 
apt clean 
rm -rf /var/cache/apt/* 
apt update -qq 
echo "$HOSTNAME repolist" > "$reportFile" 
apt-cache policy | grep http | awk '{print $2 $3}' >> "$reportFile" 
echo "$HOSTNAME repolist end" >> "$reportFile" 
echo >> "$reportFile"
echo "Available Kernels" >> "$reportFile" 
dpkg --list | grep linux-image | awk '{ print $2 }' >> "$reportFile" 
echo "Available Kernels End" >> "$reportFile" 
echo  >> "$reportFile" 
echo "Currently running kernel version is: $(uname -r)" >> "$reportFile" 
echo >> "$reportFile" 
dpkg --list | grep linux-image | awk '{ print $2 }' | grep $(uname -r) > "$kernelPackageFile" 
echo "Current CrowdStrike version is: $(/opt/CrowdStrike/falconctl -g --version)" >> "$reportFile" 
echo "Current CrowdStrike RMF-Status is: $(/opt/CrowdStrike/falconctl -g --rfm-state)" >> "$reportFile" 
echo >> "$reportFile" 
echo "Kernel packages installed" >> "$reportFile" 
cat "$kernelPackageFile" >> "$reportFile" 
echo "Kernel packages installed end" >> "$reportFile" 
echo "Drive space: " >> "$reportFile" 
df -h /var >> "$reportFile" 
clear
cat "$reportFile"
```

This script will generate a report that provides information about the device's current state, including available kernels, CrowdStrike version, and drive space.

## Evaluating the Pre-Patch Report
    1. repo check, 
        1.1 Reference this link for guidance https://one.rackspace.com/display/~todd6585/Position+Paper%3A+Navigating3.10.0-1160.99.1.el7Repository+Risks+in+Multi-Distribution+Linux+Environments
        1.2 Although this approach may not fully satisfy the requirements of Windows administrators, implementing code to check for all possible upstream repositories can be complex and time-consuming. Considering the effort required, it is important to carefully evaluate the benefits before investing significant resources.
    2. Available Kernels
        2.1 here copy a Kernel version number greater than the currently running kernel version and put it into this link: https://falcon.laggar.gcw.crowdstrike.com/documentation/page/cefbaf45/linux-supported-kernels. this will return a list of supported Crowdtrike version that are supported. 
    3. Currently Running Kernel version
        3.1 The current running Kernel version. Used to evaluate the new kernel version
    4. Current Crowdstrike Version
        4.1 The current running Crowdstrike version. used to evaluate the new kernel version
    5. Current Crowdstrike RFM State
        5.1 If this returns TRUE. This MUST be remediated. We will need to roll the devicie back to a supported kernel version. Any device with this set as true in NOT eligible for automated patching.
    6. Kernel Packages installed
        6.1 This package is used to insure that all kernel packages are all updated and is called during the execution of of the patchme.sh script.
        6.2 This should return at a minimum 2 files in Yum/DNF Instances kernel and kernel-tools and for APT instances linux-image and linux-tools packages are typical. 
        6.3 This file should NOT be empty. if it is further investigation is needed.
    7. /var Drive Space
        7.1 anything less than 3GB should be remediated
        7.2 check to see if LVM is installed and if it is and there is space available. see the help of a Linux Admin to expand the drive ASAP. this work can be done off ticket and should not delay execution or scheduling. 
        ```bash
        lvm
        pvs
        vgs
        grep var /etc/fsta
        ```
        7.3 If LVM is not installed or if there is not space on the LVM to expand the drive to 3GB, then reach out to the Patching Team to have the device removed form the ticket or to have the agency remediate further.

## Staging the Dry-Run patchme.sh script

After generating the report, update the newkernel variable in appropriate code block below with the latest kernel supported by the currently running CrowdStrike version. Check the available kernels against the list here: https://falcon.laggar.gcw.crowdstrike.com/documentation/page/cefbaf45/linux-supported-kernels. Then copy and paste that code block into the CLI.

AWSLinux1 AWSLinux2 RHEL7 and RHEL8 Version (AKA the YUM version)
```bash
echo '#!/bin/bash
newkernel="3.10.0-1160.99.1.el7"
yum --assumeno install $(while read p; do printf "%s-%s " "$p" "$newkernel"; done < /root/{ChangeNumber}/kernel_packages)' > /root/{ChangeNumber}/patchme.sh

```

AWSLinux2 RHEL8 and RHEL9 Versions (AKA the DNF version)
```bash
echo '#!/bin/bash
newkernel="{Dnf-Kernel}"
dnf --assumeno install $(while read p; do printf "$p-$newkernel "; done < /root/{ChangeNumber}/kernel_packages)' > /root/{ChangeNumber}/patchme.sh
```

Ubuntu and Debian Version (AKA the APT version)
```bash
echo '#!/bin/bash
newkernel="{Apt-Kernel}"
apt-get --simulate install $(while read p; do printf "$p-$newkernel "; done < /root/{ChangeNumber}/kernel_packages) > /root/{ChangeNumber}/patchme.sh
```

Note: We are using --assumeno and --simulate switches for dry-run mode. Execute with bash patchme.sh.

```bash
bash patchme.sh
```

If the dry-run version of the script is successful, run the appropriate command posted below to make the patchme.sh ready for execution.

```bash
# YUM/DNF devices
sed -i -e 's/--assumeno/-y/g' patchme.sh
cat patchme.sh    

# APT devices
sed -i -e 's/--simulate/-y/g' patchme.sh
cat patchme.sh
```

##  Stage the Post Patch Report

Copy and past the following the appropriate code block into the CLI to create the post-patch-report.sh. This will be run after reboot during the execution window. 

AWSLinux1 AWSLinux2 RHEL7 and RHEL8 Version (AKA the YUM version)
```bash
echo '#!/bin/bash
ChangeNumber="{ChangeNumber}" 
outputDir="/root/$ChangeNumber" 
kernelPackageFile="/root/$ChangeNumber/kernel_packages" 
reportFile="$outputDir/post-patch.report" 
mkdir -p "$outputDir" 
cd "$outputDir" 
echo "$HOSTNAME repolist" > "$reportFile" 
yum -v repolist | grep Repo-id | cut -d ":" -f2 >> "$reportFile" 
echo "$HOSTNAME repolist end" >> "$reportFile" 
echo 
echo "Available Kernels" >> "$reportFile" 
yum list kernel --showduplicates | tail >> "$reportFile" 
echo "Available Kernels End" >> "$reportFile" 
echo  >> "$reportFile" 
echo "Currently running kernel version is: $(uname -r)" >> "$reportFile" 
echo >> "$reportFile" 
yum list installed 'kernel*' | grep ^kernel | cut -d. -f1 | sort -u > "$kernelPackageFile"
echo "Current CrowdStrike version is: $(/opt/CrowdStrike/falconctl -g --version)" >> "$reportFile" 
echo "Current CrowdStrike RMF-Status is: $(/opt/CrowdStrike/falconctl -g --rfm-state)" >> "$reportFile" 
echo 
echo "Kernel packages installed" >> "$reportFile" 
cat "$kernelPackageFile" >> "$reportFile" 
echo "Kernel packages installed end" >> "$reportFile" 
echo "Drive space: " >> "$reportFile" 
df -h /var >> "$reportFile" 
rpm -qa --last | awk -v limit="$(date -d '12 hours ago' '+%s')" '{
    cmd = "date -d \"" $3 " " $4 " " $5 " " $6 "\" +%s"
    cmd | getline date
    close(cmd)
    if (date >= limit) print
}' > Installed-Packages
cat "$reportFile"' > /root/{ChangeNumber}/post-patch-report.sh
```

AWSLinux2 RHEL8 and RHEL9 Versions (AKA the DNF version)
```bash
echo '#!/bin/bash
ChangeNumber="{ChangeNumber}" 
outputDir="/root/$ChangeNumber" 
kernelPackageFile="/root/$ChangeNumber/kernel_packages" 
reportFile="$outputDir/post-patch.report" 
mkdir -p "$outputDir" 
cd "$outputDir" 
echo "$HOSTNAME repolist" > "$reportFile" 
dnf -v repolist | grep Repo-id | cut -d ":" -f2 >> "$reportFile" 
echo "$HOSTNAME repolist end" >> "$reportFile" 
echo 
echo "Available Kernels" >> "$reportFile" 
dnf list kernel --showduplicates | tail >> "$reportFile" 
echo "Available Kernels End" >> "$reportFile" 
echo  >> "$reportFile" 
echo "Currently running kernel version is: $(uname -r)" >> "$reportFile" 
echo >> "$reportFile" 
dnf list installed 'kernel*' | grep ^kernel | cut -d. -f1 | sort -u > "$kernelPackageFile"
echo "Current CrowdStrike version is: $(/opt/CrowdStrike/falconctl -g --version)" >> "$reportFile" 
echo "Current CrowdStrike RMF-Status is: $(/opt/CrowdStrike/falconctl -g --rfm-state)" >> "$reportFile" 
echo 
echo "Kernel packages installed" >> "$reportFile" 
cat "$kernelPackageFile" >> "$reportFile" 
echo "Kernel packages installed end" >> "$reportFile" 
echo "Drive space: " >> "$reportFile" 
df -h /var >> "$reportFile" 
cat "$reportFile"' > /root/{ChangeNumber}/post-patch-report.sh
```

Ubuntu and Debian Version (AKA the APT version)
```bash
echo '#!/bin/bash
ChangeNumber="{ChangeNumber}"
outputDir="/root/$ChangeNumber" 
kernelPackageFile="/root/$ChangeNumber/kernel_packages" 
reportFile="$outputDir/post-patch.report" 
cd "$outputDir" 
apt clean 
rm -rf /var/cache/apt/* 
apt update -qq 
echo "$HOSTNAME repolist" > "$reportFile" 
apt-cache policy | grep http | awk '{print $2 $3}' >> "$reportFile" 
echo "$HOSTNAME repolist end" >> "$reportFile" 
echo >> "$reportFile"
echo "Available Kernels" >> "$reportFile" 
dpkg --list | grep linux-image | awk '{ print $2 }' >> "$reportFile" 
echo "Available Kernels End" >> "$reportFile" 
echo  >> "$reportFile" 
echo "Currently running kernel version is: $(uname -r)" >> "$reportFile" 
echo >> "$reportFile" 
dpkg --list | grep linux-image | awk '{ print $2 }' | grep $(uname -r) > "$kernelPackageFile" 
echo "Current CrowdStrike version is: $(/opt/CrowdStrike/falconctl -g --version)" >> "$reportFile" 
echo "Current CrowdStrike RMF-Status is: $(/opt/CrowdStrike/falconctl -g --rfm-state)" >> "$reportFile" 
echo >> "$reportFile" 
echo "Kernel packages installed" >> "$reportFile" 
cat "$kernelPackageFile" >> "$reportFile" 
echo "Kernel packages installed end" >> "$reportFile" 
echo "Drive space: " >> "$reportFile" 
df -h /var >> "$reportFile" 
clear' > /root/$ChangeNumber/post-patch-report.sh
```

## Create QC Verification and Execution instructions for the Change Ticket

Once all devices on the Change ticket have passed QC and have had the their scripts staged, update the ticket with this template which includes the execution script for reference as well as instructions on how to patch the device at execution. Before posting ensure that you remove any patchme.sh script from the Ticket update below if there are no relevant devices for that OS on the Change:

```text
==========================================
Automated Patching. Manual QC Pass Ready for Execution
Kernel Upgrade script located in /root/{ChangeNumber}/patchmen.sh
==========================================
AWSLinux1 AWSLinux2 RHEL7 and RHEL8 Version (AKA the YUM version)
#!/bin/bash
newkernel="{NewKernel}"
yum --assumeno install $(while read p; do printf "$p-$newkernel "; done < /root/{ChangeNumber}/kernel_packages)
==========================================

Pre-Execution Qualys QC Checks
1. Qualys Job ID: 
2. Is the Qualys job set to Enabled: 
3. Confirm that the Qualys Job ends 1 hour before the Change window closes: 

Post re-boot checks.
1. Log in via SSM or SFT
2. Sudo up
# sudo -i
3. Change directory to working directory
# cd /root/{ChangeNumber}/
4. Execute post-patch-report.sh
# bash post-patch-report.sh

Ensure that we installed and rebooted to the correct kernel
Ensure that Crowdstrike is running and that the rfm state is FALSE
Ensure no other patches need be applied
Check the drive space for /var, there should be more than 3GB of space.

==========================================
```