#!/bin/bash

region="us-gov-east-1"
declare -A os_filters
declare -a results

os_filters["RHEL7"]="Name=name,Values=*RHEL-7.9_HVM*"
os_filters["RHEL8"]="Name=name,Values=*RHEL-8.7.0_HVM*"
os_filters["RHEL9"]="Name=name,Values=*RHEL-9.0.0_HVM-*"
os_filters["AL2"]="Name=name,Values=*amzn2-ami-kernel-5.10-hvm-*"
os_filters["AL2023"]="Name=name,Values=*al2023-ami-2023*"
os_filters["Ubuntu2204"]="Name=name,Values=*ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"
os_filters["Ubuntu2004"]="Name=name,Values=*ubuntu-pro-server/images/hvm-ssd/ubuntu-bionic-18.04*"

# Assuming that all AMIs in GovCloud might be under Amazon's ownership or perhaps other known ownerships.
# If this isn't the case, adjust the owner IDs as necessary.

for os in "${!os_filters[@]}"; do
  ami_id=$(aws ec2 describe-images --region $region --filters "${os_filters[$os]}" "Name=state,Values=available" "Name=architecture,Values=x86_64" --query "Images | sort_by(@, &CreationDate) | [0].ImageId" --output text)
  results+=("$os AMI: $ami_id")
done

# Sorting the results and printing
IFS=$'\n' sorted=($(sort <<<"${results[*]}"))
unset IFS
for line in "${sorted[@]}"; do
  echo "$line"
done
