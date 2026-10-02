Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "    Launching AI Prompt-to-Video Studio" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "Server starting at: http://127.0.0.1:8000" -ForegroundColor Yellow
python -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload
