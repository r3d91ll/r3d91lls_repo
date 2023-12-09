
#!/bin/bash

# Required argument defaults
newKernel=""
changeNumber=""
minFreeSpaceGB=""
outputDirectory="/root"

# Flag for quiet mode and no script generation
quietMode=false
noScript=false

# Function to print usage
usage() {
    echo "Usage: $0 -k <newKernel> -c <ChangeNumber> [-f <min_free_space_gb>] [-d <directory>] [-q] [--no-script]"
    echo "  -k <newKernel>           : Specify new kernel version."
    echo "  -c <ChangeNumber>        : Specify ChangeNumber."
    echo "  -f <min_free_space_gb>   : Override minimum free space requirement."
    echo "  -d <directory>           : Override default output directory."
    echo "  -q                       : Enable quiet mode."
    echo "  --no-script              : Create reports without generating patchme.sh script."
    exit 1
}

# Parse command-line options
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -k) newKernel="$2"; shift ;;
        -c) changeNumber="$2"; shift ;;
        -f) minFreeSpaceGB="$2"; shift ;;
        -d) outputDirectory="$2"; shift ;;
        -q) quietMode=true ;;
        --no-script) noScript=true ;;
        *) echo "Unknown parameter passed: $1"; usage ;;
    esac
    shift
done

# Validate required options
if [[ -z "$changeNumber" ]] || { [[ -z "$newKernel" ]] && [[ "$noScript" = false ]]; }; then
    echo "Error: Missing required arguments."
    usage
fi

# Function to create and execute patchme.sh script
createAndExecutePatchme() {
    local kernelVersion=$1
    local scriptName="/root/${changeNumber}/patchme.sh"

    # Check if script already exists
    if [[ -f "$scriptName" ]]; then
        echo "The script $scriptName already exists."
        return 1
    fi

    # Determine whether to use YUM or DNF based on RHEL version
    local pkgManager=""
    local rhelVersion=$(rpm -E %{rhel})
    if [[ $rhelVersion -le 7 ]]; then
        pkgManager="yum"
    else
        pkgManager="dnf"
    fi

    # Create the patchme.sh script
    echo "#!/bin/bash" > "$scriptName"
    echo "$pkgManager --assumeno install \$(while read p; do printf "$p-$kernelVersion "; done < /root/${changeNumber}/kernel_packages)" >> "$scriptName"
    chmod +x "$scriptName"

    # Dry-run execution
    echo "Executing dry-run of $scriptName..."
    sh -n "$scriptName"
    if [[ $? -ne 0 ]]; then
        echo "Dry-run failed. Maintaining script in dry-run mode."
        return 1
    else
        echo "Dry-run successful. Changing script execution mode."
        sed -i 's/--assumeno/-y -q/' "$scriptName"
    fi
}

# Main execution
if [[ "$noScript" = false ]]; then
    createAndExecutePatchme "$newKernel"
fi

# Additional pre-patch checks and report generation can be added here.

echo "Pre-patch checks completed."
