# NexusPatcher: Overview

## Introduction

NexusPatcher is a comprehensive Linux patching and quality control tool designed to facilitate kernel updates, targeted security patching, and pre/post-patch quality checks. The tool is tailored for RHEL-based systems, focusing on DNF and YUM package managers.

## Components

### DeckardClass

    Purpose: Manages kernel patching preparation and staging of scripts for patching and updates.
    Key Functions:
        perform_pre_patch_checks: Executes pre-patching quality checks.
        stage_kernel_patch_script: Generates and stages kernel update scripts.
        stage_security_patch_script: Stages patching scripts for specific CVEs and RHSAs.

### BryantClass

    Purpose: Handles targeted patching preparation based on CVEs and RHSA IDs.
    Key Functions:
        parse_input: Parses CVEs and RHSAs from various input formats.
        generate_patch_command: Creates patching commands for targeted vulnerabilities.

### MercerClass

    Purpose: Performs disk space checks as part of pre-patching preparations.
    Key Functions:
        check_disk_space: Assesses available disk space.
        report_large_files: Identifies large files if space is insufficient.

### RoyClass

    Purpose: Conducts comprehensive system quality checks pre- and post-patching.
    Key Functions:
        check_service_status: Verifies the status of critical services.
        validate_system_health: Assesses overall system health and performance.
        confirm_kernel_version: Validates the kernel version post-patch.
        review_startup_logs: Checks system logs for errors or warnings.
        test_network_connectivity: Ensures proper network communication.
        validate_disk_space: Confirms sufficient disk space post-operations.

## Packaging and Distribution

    Method: Packaged as an RPM for straightforward installation on RHEL-based systems.
    Installation Path: /opt/rackspace/racktools/NexusPatcher.

## Logging and Reporting

    Implementation: Detailed logging of all operations to /var/log/racktools/NexusPatcher.
    Integration: Logs formatted for compatibility with monitoring tools like Splunk.

## Security and Compliance

    Focus: Adheres to best practices for security and organizational compliance.
    Review Process: Regular security audits and updates to ensure ongoing compliance.
