#!/bin/bash

# Specify the date for the yum transactions
REPORT_FILE="post-patch.report"
DATE="2023-12-16"
# Format the date for exact matching
formatted_date=$(date -d "$DATE" "+%Y-%m-%d")

# Initialize report file
if [ ! -w $REPORT_FILE ]; then
    touch $REPORT_FILE
    else
    mv $REPORT_FILE $REPORT_FILE.$(date +%Y%m%d:%H:%M:%S).bak
    touch $REPORT_FILE
fi
echo "Post-Patch Report for $DATE" > "$REPORT_FILE"
echo "--------------------------------------" >> "$REPORT_FILE"

# Loop through each transaction ID and append to report file
echo "###Packages Patched by Qualys" | tee -a "$REPORT_FILE"
# Get the list of transaction IDs for the specified date
transaction_ids=$(yum history | awk -v date="$formatted_date" '$0 ~ date {if (match($0, /[[:space:]]+[0-9]+[[:space:]]/)) print substr($0, RSTART, RLENGTH)}')
for id in $transaction_ids;  do
    yum history info "$id" | egrep "Updated|Upgraded" | awk 'NF{print $2}' | tee -a "$REPORT_FILE"
done
# Check for available security updates and append to report file
echo "###Security Updates NOT installed by Qualys:" | tee -a "$REPORT_FILE"
for i in $(yum --security check-update | awk 'NF {print $1, $2}' | egrep -v "^-->|^Loaded|package" | cut -d. -f1); do
    yum -q updateinfo list available $i | tee -a "$REPORT_FILE"
done
