## AWS GetThatAMI.sh Script

This script helps in retrieving the latest Amazon Machine Image (AMI) IDs for popular Linux distributions available on AWS.

### How to Use

1. Ensure you have the AWS CLI installed and configured with the necessary permissions.
2. Make the script executable:

   ```bash
   chmod +x getthatami.sh
   ```

3. Run the script:

   ```bash
   ./getthatami.sh
   ```

The script will output the latest AMI IDs for the Linux distributions specified within the script.

### Extending the Script for Other Distributions

To extend the script for other Linux or Windows distributions:

1. **Determine the naming pattern**: AMIs typically have a naming pattern that distinguishes them from other images. You'll need to know this naming pattern to define your filter. For example, Ubuntu 20.04 AMIs might have a pattern like `ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server*`.

2. **Identify the owner**: Official AMIs are typically owned by a specific AWS account. For example, official Ubuntu AMIs are owned by Canonical's AWS account `099720109477`.

3. **Add to the `os_filters` array**: Update the `os_filters` associative array in the script with a new key for your distribution and a filter pattern that matches its naming convention. For example:

   ```bash
   os_filters["YourDistName"]="Name=name,Values=your-pattern*"
   ```

4. **Modify the loop (if necessary)**: If your distribution is owned by a different account, or if there are other special considerations, modify the loop in the script to handle these cases.

For Windows, the process is similar, but the naming patterns and owners might differ. It's recommended to check AWS documentation or the EC2 console to get an idea of the naming patterns used for Windows AMIs.

### License

This script is provided "as-is" without any warranties. Use at your own risk.

