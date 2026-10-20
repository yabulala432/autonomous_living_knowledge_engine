# Script to install pgvector into PostgreSQL 18 on Windows
param(
    [string]$PgPath = "C:\Program Files\PostgreSQL\18",
    [string]$SourcePath = "$env:TEMP\vector_pg18"
)

# Ensure administrator privileges
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Elevating permissions to install extension files into Program Files..." -ForegroundColor Yellow
    Start-Process powershell.exe -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

Write-Host "Stopping PostgreSQL 18 service..." -ForegroundColor Cyan
Stop-Service -Name "postgresql-x64-18" -ErrorAction SilentlyContinue

Write-Host "Copying pgvector files to $PgPath..." -ForegroundColor Cyan
Copy-Item -Path "$SourcePath\lib\*" -Destination "$PgPath\lib\" -Force
Copy-Item -Path "$SourcePath\share\extension\*" -Destination "$PgPath\share\extension\" -Force
if (Test-Path "$SourcePath\include\server\extension\vector") {
    $includeDest = "$PgPath\include\server\extension\vector"
    New-Item -ItemType Directory -Path $includeDest -Force | Out-Null
    Copy-Item -Path "$SourcePath\include\server\extension\vector\*" -Destination $includeDest -Force
}

Write-Host "Restarting PostgreSQL 18 service..." -ForegroundColor Cyan
Start-Service -Name "postgresql-x64-18"

Write-Host "pgvector installed successfully!" -ForegroundColor Green
Start-Sleep -Seconds 2
