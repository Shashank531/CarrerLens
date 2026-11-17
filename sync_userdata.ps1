# CareerLens - Live Cloud Data Synchronizer (PowerShell Native)
param (
    [string]$CloudUrl = "https://carrerlens-a3dl.onrender.com",
    [switch]$Auto
)

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $RootDir) { $RootDir = Get-Location }

$UserDataDir = Join-Path $RootDir "data\userdata"
$CsvDir = Join-Path $RootDir "data\csv"

# Ensure directories exist
if (-not (Test-Path $UserDataDir)) { New-Item -ItemType Directory -Path $UserDataDir -Force | Out-Null }
if (-not (Test-Path $CsvDir)) { New-Item -ItemType Directory -Path $CsvDir -Force | Out-Null }

function Sync-CareerLensData {
    Write-Host "`n[Sync] Connecting to $CloudUrl ..." -ForegroundColor Cyan

    # 1. Fetch userdata.csv
    try {
        $userdata = Invoke-RestMethod -Uri "$CloudUrl/api/userdata/csv" -Method Get -TimeoutSec 30
        $userdata | Out-File -FilePath (Join-Path $UserDataDir "userdata.csv") -Encoding utf8
        $userdata | Out-File -FilePath (Join-Path $CsvDir "userdata.csv") -Encoding utf8
        $userdata | Out-File -FilePath (Join-Path $RootDir "data\userdata.csv") -Encoding utf8

        $lines = ($userdata.Trim() -split "`n") | Where-Object { $_.Trim() -ne "" }
        $userCount = [Math]::Max(0, $lines.Count - 1)
        Write-Host "  ✓ Synced userdata.csv ($userCount total users)" -ForegroundColor Green

        if ($lines.Count -gt 1) {
            $lastUser = ($lines[-1] -split ",")[2]
            $lastCode = ($lines[-1] -split ",")[1]
            Write-Host "    Latest User: $lastUser [$lastCode]" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ✗ Failed to sync userdata.csv: $($_.Exception.Message)" -ForegroundColor Red
    }

    # 2. Fetch user_attempts.csv
    try {
        $attempts = Invoke-RestMethod -Uri "$CloudUrl/api/userdata/attempts/csv" -Method Get -TimeoutSec 30
        $attempts | Out-File -FilePath (Join-Path $UserDataDir "user_attempts.csv") -Encoding utf8
        $attempts | Out-File -FilePath (Join-Path $CsvDir "user_attempts.csv") -Encoding utf8

        $aLines = ($attempts.Trim() -split "`n") | Where-Object { $_.Trim() -ne "" }
        $attemptCount = [Math]::Max(0, $aLines.Count - 1)
        Write-Host "  ✓ Synced user_attempts.csv ($attemptCount total attempts)" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Failed to sync user_attempts.csv: $($_.Exception.Message)" -ForegroundColor Red
    }

    Write-Host "[Sync] Local data files successfully updated!`n" -ForegroundColor Cyan
}

if ($Auto) {
    Write-Host "Starting Auto-Sync loop every 60 seconds (Press Ctrl+C to stop)..." -ForegroundColor Yellow
    while ($true) {
        Sync-CareerLensData
        Start-Sleep -Seconds 60
    }
} else {
    Sync-CareerLensData
}
