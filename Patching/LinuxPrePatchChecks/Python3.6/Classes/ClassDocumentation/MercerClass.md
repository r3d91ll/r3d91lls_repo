# MercerClass Overview

## Introduction

MercerClass is an integral component of the NexusPatcher tool, focused on monitoring and managing disk space as part of the pre-patching process. It ensures that adequate disk space is available before proceeding with updates, thereby reducing the risk of patching failures due to insufficient space.

## Key Responsibilities

### Disk Space Check

- Function: `check_disk_space`
- Description: Determines the total, used, and available disk space on the system. This function is crucial for ensuring that there is enough space for patching operations.
- Output: A report detailing the disk space status, which is used to decide whether to proceed with patching.

### Reporting Large Files

- Function: `report_large_files`
- Description: Identifies and reports the largest files or directories when disk space is insufficient. This feature assists in managing disk space more effectively, especially in cases where cleaning up or reallocating space is necessary before patching.
- Output: A list of large files or directories that could be candidates for cleanup to free up space.

### Integration with Other Components

- DeckardClass: The disk space check results from MercerClass are utilized by DeckardClass to determine the system's readiness for patching.
- RoyClass: Can be used post-patching to ensure that disk space is still adequate after the update process.

## Packaging and Installation

- Location: Part of the NexusPatcher suite, installed at `/opt/rackspace/racktools/NexusPatcher`.
- Usage Context: Primarily used during the pre-patching phase but can be invoked independently for general disk space management.

## Logging and Reporting

- Logging: Captures detailed logs of disk space assessments and actions taken in response to space constraints.
- Path: Logs are stored in `/var/log/racktools/NexusPatcher`, consistent with the overarching logging strategy of the tool.

## Security and Compliance

- Data Handling: Ensures that the analysis and reporting of disk space data are conducted securely, maintaining the integrity and confidentiality of system information.
- Compliance with Standards: Adheres to organizational standards and best practices for system maintenance and monitoring.
