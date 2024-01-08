# DeckardClass Overview

## Introduction

DeckardClass is a central component of the NexusPatcher tool, responsible for managing kernel patching preparation and staging of patching scripts. It ensures that all necessary quality checks are performed before any patching process begins and that the system is ready for updates.

## Key Responsibilities

### Pre-Patch Checks

- Function: `perform_pre_patch_checks`
- Description: Executes a series of quality control checks to ensure the system is in a suitable state for patching. This includes verifying disk space (integrating with MercerClass), checking system health, and ensuring critical services are running.
- Output: A report detailing the results of the pre-patch checks, indicating whether the system is ready for patching.

### Staging Kernel Patch Script

- Function: `stage_kernel_patch_script`
- Description: Generates and stages a script for kernel updates based on the current system's requirements. This script is named `patchme.sh` and is placed in `/root/{ChangeNumber}`.
- Output: The `patchme.sh` script ready for execution during the scheduled patching window.

### Staging Security Patch Script

- Function: `stage_security_patch_script`
- Description: Prepares scripts for targeted patching based on specific CVEs and RHSA IDs provided by the BryantClass. It ensures that only relevant updates are staged for patching.
- Output: Scripts tailored for addressing the specified security advisories.

### Integration with Other Components

- BryantClass: Receives input from BryantClass for targeted security patches.
- MercerClass: Utilizes MercerClass for disk space checks as part of the pre-patch validation process.
- RoyClass: Can trigger RoyClass for additional system checks if required.

## Packaging and Installation

- Location: Part of the NexusPatcher package, located in `/opt/rackspace/racktools/NexusPatcher`.
- Dependencies: Works in conjunction with other NexusPatcher components, ensuring a cohesive patching preparation process.

## Logging and Reporting

- Logging: Records detailed logs of all operations, decisions, and outcomes, aiding in transparency and troubleshooting.
- Path: Logs are stored in `/var/log/racktools/NexusPatcher` for easy access and monitoring.

## Security and Compliance

- Best Practices: Adheres to security best practices in script generation and system checks.
- Audits: Regularly reviewed to ensure compliance with the latest security standards and organizational policies.
