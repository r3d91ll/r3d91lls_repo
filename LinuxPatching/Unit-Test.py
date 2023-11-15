import pytest
from unittest.mock import patch, MagicMock
from LinuxPrePatchChecks-RHEL89-version3 import PrePatchCheck, CriticalSubprocessError
from datetime import datetime

# Constants for tests
CHANGE_NUMBER = "CN123456"
VALID_KERNEL_VERSIONS = {"RHEL/CentOS": "3.10.0-1160.31.1.el7", "Fedora": "5.11.12-300.fc34", "AWSLinux2": "4.14.225-169.362.amzn2"}
VALID_REPOS = ["base", "updates", "extras"]
INSTANCE_ID = "i-0abcdef1234567890"
OS_TYPE = "RHEL/CentOS"
AVAILABLE_KERNELS = ["kernel-3.10.0-1160.31.1.el7", "kernel-3.10.0-1160.25.1.el7"]
KERNEL_PACKAGES = "kernel-3.10.0-1160.31.1.el7"
CROWDSTRIKE_VERSION = "6.18.13603.0 (LTS)"
RFM_STATE = "False"
DISK_SPACE_GB = 10.0
CRITICAL_FAILURE_MESSAGE = "Critical Python Failure. Check logs for details."

# Helper functions for mocking
def mock_urlopen_read(url):
    if "linux-kernels.json" in url:
        return json.dumps({"kernel_list": VALID_KERNEL_VERSIONS, "valid_repos": VALID_REPOS}).encode()
    elif "instance-id" in url:
        return INSTANCE_ID.encode()
    else:
        raise ValueError("Invalid URL")

def mock_subprocess_check_output(cmd, universal_newlines=True):
    if "list available kernel*" in cmd:
        return "\n".join(AVAILABLE_KERNELS)
    elif "list updates kernel*" in cmd:
        return KERNEL_PACKAGES
    elif ["/opt/CrowdStrike/falconctl", "-g", "--version"] == cmd:
        return CROWDSTRIKE_VERSION
    elif ["/opt/CrowdStrike/falconctl", "-g", "--rfm-state"] == cmd:
        return RFM_STATE
    else:
        raise subprocess.CalledProcessError(returncode=1, cmd=cmd, output="Error")

def mock_statvfs(path):
    class MockStatvfs:
        f_frsize = 4096
        f_bavail = DISK_SPACE_GB * 1024 * 1024 * 1024 // f_frsize
    return MockStatvfs()

# Test cases
@pytest.mark.parametrize(
    "test_id, change_number, expected_kernel_versions, expected_valid_repos, expected_instance_id, expected_os_type, expected_available_kernels, expected_kernel_packages, expected_crowdstrike_version, expected_rfm_state, expected_disk_space_gb, expected_critical_failure",
    [
        # Happy path tests
        ("HP_01", CHANGE_NUMBER, VALID_KERNEL_VERSIONS, VALID_REPOS, INSTANCE_ID, OS_TYPE, AVAILABLE_KERNELS, KERNEL_PACKAGES, CROWDSTRIKE_VERSION, RFM_STATE, DISK_SPACE_GB, None),
        
        # Edge cases
        ("EC_01", CHANGE_NUMBER, {}, [], INSTANCE_ID, "Unknown", [], None, "CrowdStrike not installed", "Unknown", 0.0, None),
        
        # Error cases
        ("ER_01", CHANGE_NUMBER, VALID_KERNEL_VERSIONS, VALID_REPOS, INSTANCE_ID, OS_TYPE, AVAILABLE_KERNELS, KERNEL_PACKAGES, CROWDSTRIKE_VERSION, RFM_STATE, DISK_SPACE_GB, CRITICAL_FAILURE_MESSAGE),
    ]
)
def test_pre_patch_check(test_id, change_number, expected_kernel_versions, expected_valid_repos, expected_instance_id, expected_os_type, expected_available_kernels, expected_kernel_packages, expected_crowdstrike_version, expected_rfm_state, expected_disk_space_gb, expected_critical_failure, monkeypatch):
    # Arrange
    monkeypatch.setattr(urllib.request, 'urlopen', MagicMock(side_effect=mock_urlopen_read))
    monkeypatch.setattr(subprocess, 'check_output', MagicMock(side_effect=mock_subprocess_check_output))
    monkeypatch.setattr(os, 'statvfs', MagicMock(side_effect=mock_statvfs))
    monkeypatch.setattr(logging, 'basicConfig', MagicMock())
    monkeypatch.setattr(os, 'makedirs', MagicMock())
    monkeypatch.setattr(os.path, 'isfile', MagicMock(return_value=True))
    monkeypatch.setattr('builtins.open', MagicMock())
    monkeypatch.setattr(sys, 'exit', MagicMock())

    # Act
    pre_patch_check = PrePatchCheck(change_number)

    # Assert
    assert pre_patch_check.changeNumber == change_number
    assert pre_patch_check.kernelVersions == expected_kernel_versions
    assert pre_patch_check.validRepositories == expected_valid_repos
    assert pre_patch_check.get_instanceId() == expected_instance_id
    assert pre_patch_check.identify_os() == expected_os_type
    assert pre_patch_check.get_available_kernels() == expected_available_kernels
    assert pre_patch_check.get_kernelPackages() == expected_kernel_packages
    assert pre_patch_check.get_crowdstrikeVersion() == expected_crowdstrike_version
    assert pre_patch_check.get_rfmState() == expected_rfm_state
    assert float(pre_patch_check.csvOutput[-1].split()[0]) == expected_disk_space_gb
    if expected_critical_failure:
        with open(pre_patch_check.prePatchReportFilepath, 'r') as f:
            assert f.read() == expected_critical_failure
