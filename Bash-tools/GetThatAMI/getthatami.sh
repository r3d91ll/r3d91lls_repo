#!/bin/bash

declare -A os_filters
declare -a results

os_filters["RHEL7"]="Name=name,Values=RHEL-7.*x86_64*"
os_filters["RHEL8"]="Name=name,Values=RHEL-8.*x86_64*"
os_filters["RHEL9"]="Name=name,Values=RHEL-9.*x86_64*"
os_filters["AL2"]="Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2"
os_filters["AL2023"]="Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2"
os_filters["Ubuntu2004"]="Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server*"
os_filters["Ubuntu2204"]="Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-*22.04*-amd64-server*"

for os in "${!os_filters[@]}"; do
  if [[ $os == "Ubuntu2004" || $os == "Ubuntu2204" ]]; then
    ami_id=$(aws ec2 describe-images --owners 099720109477 --filters "${os_filters[$os]}" "Name=state,Values=available" --query "Images | sort_by(@, &CreationDate) | [-1].ImageId" --output text)
  elif [[ $os == "RHEL7" || $os == "RHEL8" || $os == "RHEL9" ]]; then
    ami_id=$(aws ec2 describe-images --owners 309956199498 --filters "${os_filters[$os]}" "Name=state,Values=available" --query "Images | sort_by(@, &CreationDate) | [-1].ImageId" --output text)
  else
    ami_id=$(aws ec2 describe-images --owners amazon --filters "${os_filters[$os]}" "Name=state,Values=available" --query "Images | sort_by(@, &CreationDate) | [-1].ImageId" --output text)
  fi
  results+=("$os AMI: $ami_id")
done

# Sorting the results and printing
IFS=$'\n' sorted=($(sort <<<"${results[*]}"))
unset IFS
for line in "${sorted[@]}"; do
  echo "$line"
done
