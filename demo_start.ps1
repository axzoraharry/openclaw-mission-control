# Quick Demo Start Script for Windows PowerShell
# Save as: demo_start.ps1

Write-Host "🎯 OpenClaw Mission Control - Demo Mode Quick Start" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""

Write-Host "🚀 Starting Demo Environment..." -ForegroundColor Yellow
Write-Host ""

# Check if services are running
Write-Host "1. Checking backend status..." -ForegroundColor Cyan
try {
    $backendStatus = Invoke-WebRequest -Uri "http://localhost:8000/healthz" -UseBasicParsing -ErrorAction Stop
    if ($backendStatus.StatusCode -eq 200) {
        Write-Host "   ✅ Backend is running" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ Backend not running - starting..." -ForegroundColor Red
    Set-Location "backend"
    Start-Process -NoNewWindow -FilePath "uv" -ArgumentList "run", "uvicorn", "app.main:app", "--reload", "--port", "8000"
    Start-Sleep -Seconds 5
    Set-Location ".."
}

Write-Host ""
Write-Host "2. Checking frontend status..." -ForegroundColor Cyan
try {
    $frontendStatus = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -ErrorAction Stop
    if ($frontendStatus.StatusCode -eq 200) {
        Write-Host "   ✅ Frontend is running" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ Frontend not running - starting..." -ForegroundColor Red
    Set-Location "frontend"
    Start-Process -NoNewWindow -FilePath "npm" -ArgumentList "run", "dev"
    Start-Sleep -Seconds 5
    Set-Location ".."
}

Write-Host ""
Write-Host "3. Verifying demo mode..." -ForegroundColor Cyan
$envFile = "frontend\.env"
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Raw
    if ($envContent -match "NEXT_PUBLIC_DEMO_MODE=true") {
        Write-Host "   ✅ Demo mode is enabled" -ForegroundColor Green
    } else {
        Write-Host "   ⚠  Demo mode not enabled - enabling..." -ForegroundColor Yellow
        Add-Content $envFile "`nNEXT_PUBLIC_DEMO_MODE=true"
    }
} else {
    Write-Host "  ⚠ .env file not found - creating with demo mode..." -ForegroundColor Yellow
    Set-Content $envFile "NEXT_PUBLIC_DEMO_MODE=true"
}

Write-Host ""
Write-Host "4. Opening Mission Control..." -ForegroundColor Cyan
Write-Host "   🌐 Access URLs:" -ForegroundColor White
Write-Host "    - Local:  http://localhost:3000" -ForegroundColor White
Write-Host "    - Network: http://192.168.29.250:3000" -ForegroundColor White
Write-Host ""
Write-Host "  🎯 Demo Features:" -ForegroundColor White
Write-Host "    - No login required" -ForegroundColor White
Write-Host "    - Yellow banner shows 'Demo Mode Active'" -ForegroundColor White
Write-Host "    - Pre-authenticated with valid token" -ForegroundColor White
Write-Host ""

# Open browser
Write-Host "  🔍 Opening browser..." -ForegroundColor Yellow
Start-Process "http://localhost:3000"

Write-Host "✅ Demo environment is ready!" -ForegroundColor Green
Write-Host "Look for the yellow 'Demo Mode Active' banner at the top of the page." -ForegroundColor White
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Yellow
Write-Host "1. Explore the Activity Feed" -ForegroundColor White
Write-Host "2. Visit your 'Mr. Happy Digital CEO Board'" -ForegroundColor White
Write-Host "3. Check the Agents dashboard" -ForegroundColor White
Write-Host "4. Try creating a test task" -ForegroundColor White
Write-Host ""
Write-Host "🔧 For troubleshooting, check:" -ForegroundColor Yellow
Write-Host "- Browser console (F12)" -ForegroundColor White
Write-Host "- Backend logs in terminal" -ForegroundColor White
Write-Host "- Demo mode banner visibility" -ForegroundColor White
Write-Host ""

Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")