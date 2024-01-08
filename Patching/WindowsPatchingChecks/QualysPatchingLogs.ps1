# Define the start and end dates
$startDate = [DateTime]::Parse("12/22/2023")
$endDate = [DateTime]::Parse("12/23/2023").AddDays(1) # Include all of 12/23

# Path to the log file
$logFilePath = "C:\ProgramData\Qualys\QualysAgent\Logs\Patch\patchlog.txt"

# Define the output file path (change this to a valid path on your system)
$outputFilePath = "C:\Users\pcmsft_todd_bucy\patchlog.txt"

# Read the log file and select lines based on the date range
Get-Content $logFilePath | Where-Object {
    # Attempt to parse the date from each line
    if ($_ -match '\d{2}/\d{2}/\d{4}') {
        $date = [DateTime]::Parse($matches[0])
        # Include the line if it's within the date range
        $date -ge $startDate -and $date -lt $endDate
    }
} | Out-File $outputFilePath
gc $outputFilePath
