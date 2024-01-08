param (
    [Parameter(Mandatory=$true, Position=0)]
    [string]$changeNumber
)
$hostname = hostname
$workingDirectory = "C:\rspkgs\$changeNumber"
if (-not (Test-Path -Path $workingDirectory)) {
    New-Item -ItemType Directory -Path $workingDirectory -Force
}
function CheckEventLogEventIDExists {
    param(
        [string]$logName,
        [int]$eventID,
        [int]$lastDays)
    $dateLimit = (Get-Date).AddDays(-$lastDays)
    $events = Get-WinEvent -FilterHashtable @{LogName=$logName; ID=$eventID; StartTime=$dateLimit} 
    return [bool]($events)
}
function CheckSystemReboot {
    $dateLimit = (Get-Date).AddDays(-30)
    $lastBootUpTime = (Get-CimInstance -ClassName Win32_OperatingSystem).LastBootUpTime
    return [bool]($lastBootUpTime -gt $dateLimit)
}
function CheckDiskSpace {
    $disk = Get-CimInstance -ClassName Win32_LogicalDisk -Filter "DeviceID='C:'"
    $freeSpaceGB = [math]::Round($disk.FreeSpace / 1GB, 2)
    return [bool]($freeSpaceGB -gt 20)
}
$event2004Exists = CheckEventLogEventIDExists -logName "System" -eventID 2004 -lastDays 30
$event19Exists = CheckEventLogEventIDExists -logName "System" -eventID 19 -lastDays 30
$event22Exists = CheckEventLogEventIDExists -logName "System" -eventID 22 -lastDays 30
$systemRebooted = CheckSystemReboot
$diskSpaceOk = CheckDiskSpace
Write-Host "1. Were there resource exhaustion warnings in the last 30 days (Event ID 2004 exists)? $event2004Exists"
Write-Host "2. Were Windows updates installed in the last 30 days (Event ID 19 exists)? $event19Exists"
Write-Host "3. Was the System Rebooted in the Last 30 Days? $systemRebooted"
Write-Host "4. Does the C: Drive have more than 20GB Available Space? $diskSpaceOk"
Write-Host "5. Was Event ID 22 Logged in the Last 30 Days? $event22Exists"
Write-Host "6. Latest Four Installed Hotfixes:"
$hotfixes = Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 4
foreach ($hotfix in $hotfixes) {
    Write-Host " - $($hotfix.HotFixID) installed on: $($hotfix.InstalledOn)"
}
if ($event22Exists -and -not $event19Exists) {
    Write-Host "$hostname should be rebooted before patching"
}
$outputObject = [PSCustomObject]@{
    "Resource Exhaustion Warnings (Event ID 2004)" = $event2004Exists
    "Windows Updates Installed (Event ID 19)" = $event19Exists
    "System Rebooted in Last 30 Days" = $systemRebooted
    "C: Drive > 20GB Free Space" = $diskSpaceOk
    "Event ID 22 Logged in Last 30 Days" = $event22Exists
}
$outputObject | Export-Csv -Path $outputPath -NoTypeInformation
Write-Host "Output also saved to CSV: $outputPath"

