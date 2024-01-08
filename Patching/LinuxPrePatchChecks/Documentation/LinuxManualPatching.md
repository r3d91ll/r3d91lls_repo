# Manual Patching of Linux Devices

This document outlines the process for manually patching RHEL, AWSLinux, and Ubuntu devices by the PCM-Ops team. The procedure involves preparing a device for patching, generating a report, and updating a Ticket. The Ticket update will confirm that the Change has been QC'ed and provide instructions for patching the device at execution.

Pro-Tip: Copy the raw version of this document into a text editor and use find-and-replace for "{Change-Number}" to update all commands with the correct directory and change number. When you find the correct kernel, do another find-and-replace on the current value of the newkernel variable to update all relevant scripts and the Ticket Update.

## Creating the Pre-Patch Report

Update the ChangeNumber variable in the appropriate code below to match the change number you are working out of. Then, copy and paste the code into the CLI of the device you're preparing for patching.

AWSLinux1 AWSLinux2 RHEL7 and RHEL8 Version (AKA the YUM version)
```bash
sudo -i
ChangeNumber="{Change-Number}" 
outputDir="/root/$ChangeNumber" 
kernelPackageFile="/root/$ChangeNumber/kernel_packages" 
reportFile="$outputDir/pre-patch.report" 
rm -rf "$outputDir"
mkdir -p "$outputDir" 
cd "$outputDir" 
yum clean all 
rm -rf /var/cache/yum/* 
yum makecache -q 
echo "$HOSTNAME repolist" > "$reportFile" 
yum -v repolist | grep Repo-id | cut -d ":" -f2 >> "$reportFile" 
echo "$HOSTNAME repolist end" >> "$reportFile" 
echo 
echo "Available Kernels" >> "$reportFile" 
yum list kernel --showduplicates | tail >> "$reportFile" 
echo "Available Kernels End" >> "$reportFile" 
echo 
echo "Currently running kernel version is: $(uname -r)" >> "$reportFile" 
echo 
yum list installed 'kernel*' | grep ^kernel | cut -d. -f1 | sort -u > "$kernelPackageFile"
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

AWSLinux2 RHEL8 and RHEL9 Versions (AKA the DNF version)
```bash
sudo -i
ChangeNumber="{Change-Number}" 
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
ChangeNumber="{Change-Number}" 
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

## Staging the Dry-Run patchme.sh script

After generating the report, update the newkernel variable in appropriate code block below with the latest kernel supported by the currently running CrowdStrike version. Check the available kernels against the list here: https://falcon.laggar.gcw.crowdstrike.com/documentation/page/cefbaf45/linux-supported-kernels. Then copy and paste that code block into the CLI.

AWSLinux1 AWSLinux2 RHEL7 and RHEL8 Version (AKA the YUM version)
```bash
echo '#!/bin/bash
newkernel="{Yum-Kernel}"
yum --assumeno install $(while read p; do printf "$p-$newkernel "; done < /root/{Change-Number}/kernel_packages)
yum --assumeno --security --exclude "kernel*" update ' > /root/{Change-Number}/patchme.sh
```

AWSLinux2 RHEL8 and RHEL9 Versions (AKA the DNF version)
```bash
echo '#!/bin/bash
newkernel="{Dnf-Kernel}"
dnf --assumeno install $(while read p; do printf "$p-$newkernel "; done < /root/{Change-Number}/kernel_packages)
# For security updates, ensure the dnf-plugins-core package is installed and the security plugin is enabled
dnf --assumeno --security --exclude "kernel*" update ' > /root/{Change-Number}/patchme.sh
```

Ubuntu and Debian Version (AKA the APT version)
```bash
echo '#!/bin/bash
newkernel="{Apt-Kernel}"
apt-get --simulate install $(while read p; do printf "$p-$newkernel "; done < /root/{Change-Number}/kernel_packages)
apt-get --simulate upgrade --only-upgrade' > /root/{Change-Number}/patchme.sh
```

Note: We are using --assumeno and --simulate switches for dry-run mode. Execute with bash patchme.sh.

```bash
bash patchme.sh
```

If the dry-run version of the script is successful, run the following command to to change the --assumeno switch to a -y. After this command the patchme.sh should not be run until execution:

```bash
sed -i -e 's/--assumeno/-y/g' patchme.sh
cat patchme.sh
```

##  Stage the Post Patch Report

Copy and past the following the appropriate code block into the CLI to create the post-patch-report.sh. This will be run after reboot during the execution window. 

AWSLinux1 AWSLinux2 RHEL7 and RHEL8 Version (AKA the YUM version)
```bash
echo '#!/bin/bash
ChangeNumber="{Change-Number}" 
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
cat "$reportFile"' > /root/{Change-Number}/post-patch-report.sh
```

AWSLinux2 RHEL8 and RHEL9 Versions (AKA the DNF version)
```bash
echo '#!/bin/bash
ChangeNumber="{Change-Number}" 
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
cat "$reportFile"' > /root/{Change-Number}/post-patch-report.sh
```

Ubuntu and Debian Version (AKA the APT version)
```bash
echo '#!/bin/bash
ChangeNumber="{Change-Number}" 
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
clear' > /root/{Change-Number}/post-patch-report.sh
```

## Create QC Verification and Execution instructions for the Change Ticket

Once all devices on the Change ticket have passed QC and have had the their scripts staged, update the ticket with this template which includes the execution script for reference as well as instructions on how to patch the device at execution. Before posting ensure that you remove any patchme.sh script from the Ticket update below if there are no relevant devices for that OS on the Change:

```text
==========================================
Manual Patching. QC Pass Ready for Execution
Execution script located in /root/{Change-Number}/patchmen.sh
==========================================
AWSLinux1 AWSLinux2 RHEL7 and RHEL8 Version (AKA the YUM version)
echo '#!/bin/bash
newkernel="{Yum-Kernel}"
yum --assumeno install $(while read p; do printf "$p-$newkernel "; done < /root/{Change-Number}/kernel_packages)
yum --assumeno --security --exclude "kernel*" update ' > /root/{Change-Number}/patchme.sh
bash patchme.sh

AWSLinux2 RHEL8 and RHEL9 Versions (AKA the DNF version)
#!/bin/bash
newkernel="{Dnf-Kernel}"
dnf --assumeno install $(while read p; do printf "$p-$newkernel "; done < /root/{Change-Number}/kernel_packages)
dnf --assumeno --security --exclude "kernel*" update

Ubuntu and Debian Version (AKA the APT version)
#!/bin/bash
newkernel="{Apt-Kernel}"
apt-get --simulate install $(while read p; do printf "$p-$newkernel "; done < /root/{Change-Number}/kernel_packages)
apt-get --simulate upgrade --only-upgrade
==========================================

Execution
1. Log in via SSM or SFT
2. Sudo up
# sudo -i
3. Change directory
# cd /root/{Change-Number}/
4. Execute patchme.sh
# bash patchme.sh
5. Reboot
# reboot


Post re-boot checks.
1. Log in via SSM or SFT
2. Sudo up
# sudo -i
3. Change directory to working directory
# cd /root/{Change-Number}/
4. Execute post-patch-report.sh
# bash post-patch-report.sh

Ensure that we installed and rebooted to the correct kernel
Ensure that Crowdstrike is running and that the rfm state is FALSE
Ensure no other patches need be applied
Check the drive space for /var, there should be more than 3GB of space.

==========================================
```