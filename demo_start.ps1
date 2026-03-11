# Quick Demo Start Script for Windows PowerShell
# Axzora Mission Control - Full AI Stack Demo

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║        AXZORA MISSION CONTROL - AI DEMO QUICK START             ║" -ForegroundColor Green
Write-Host "║        Mr Happy AI + Voice + Agents + Mission Control            ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "🚀 Starting AI Demo Environment..." -ForegroundColor Yellow
Write-Host ""

# Check Ollama (LLM backend)
Write-Host "1. Checking Ollama LLM..." -ForegroundColor Cyan
try {
    $ollamaStatus = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -ErrorAction Stop
    if ($ollamaStatus.StatusCode -eq 200) {
        Write-Host "   ✅ Ollama is running" -ForegroundColor Green
    }
} catch {
    Write-Host "   ⚠  Ollama not running - AI features will use fallback" -ForegroundColor Yellow
    Write-Host "   Install: https://ollama.ai then run: ollama pull llama3.2:3b" -ForegroundColor Gray
}

# Check backend
Write-Host ""
Write-Host "2. Checking backend status..." -ForegroundColor Cyan
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

# Check Mr Happy Agent
Write-Host ""
Write-Host "3. Checking Mr Happy AI Agent..." -ForegroundColor Cyan
try {
    $agentStatus = Invoke-WebRequest -Uri "http://localhost:8001/health" -UseBasicParsing -ErrorAction Stop
    if ($agentStatus.StatusCode -eq 200) {
        Write-Host "   ✅ Mr Happy Agent is running" -ForegroundColor Green
    }
} catch {
    Write-Host "   ⚠  Mr Happy Agent not running - starting..." -ForegroundColor Yellow
    Start-Process -NoNewWindow -FilePath "python" -ArgumentList "skills/agent_services.py", "start", "mr_happy"
    Start-Sleep -Seconds 3
}

# Check Voice Server
Write-Host ""
Write-Host "4. Checking Voice WebSocket Server..." -ForegroundColor Cyan
try {
    $voiceStatus = Invoke-WebRequest -Uri "http://localhost:8765" -UseBasicParsing -ErrorAction Stop -TimeoutSec 2
    Write-Host "   ✅ Voice server is running" -ForegroundColor Green
} catch {
    Write-Host "   ⚠  Voice server not running - start manually if needed" -ForegroundColor Yellow
    Write-Host "   Run: python axzora-ai/mr-happy/voice_integrated.py --ws" -ForegroundColor Gray
}

# Check frontend
Write-Host ""
Write-Host "5. Checking frontend status..." -ForegroundColor Cyan
try {
    $frontendStatus = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -ErrorAction Stop
    if ($frontendStatus.StatusCode -eq 200) {
        Write-Host "   ✅ Frontend is running" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ Frontend not running - starting..." -ForegroundColor Red
    Set-Location "frontend"
    Start-Process -NoNewWindow -FilePath "cmd.exe" -ArgumentList "/c", "npm", "run", "dev"
    Start-Sleep -Seconds 8
    Set-Location ".."
}

Write-Host ""
Write-Host "6. Verifying demo mode..." -ForegroundColor Cyan
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
    Write-Host "   ⚠ .env file not found - creating with demo mode..." -ForegroundColor Yellow
    Set-Content $envFile "NEXT_PUBLIC_DEMO_MODE=true`
NEXT_PUBLIC_VOICE_WS=ws://localhost:8765`
NEXT_PUBLIC_MR_HAPPY_URL=http://localhost:8001"
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                    ✅ SYSTEM READY                                ║" -ForegroundColor Green
Write-Host "╠══════════════════════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║  Service                    │ URL                                ║" -ForegroundColor Green
Write-Host "╠═════════════════════════════╪════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║  🎨 Mission Control UI      │ http://localhost:3000              ║" -ForegroundColor White
Write-Host "║  🔧 Backend API             │ http://localhost:8000/docs         ║" -ForegroundColor White
Write-Host "║  🤖 Mr Happy Agent          │ http://localhost:8001/chat         ║" -ForegroundColor White
Write-Host "║  🎙️  Voice WebSocket         │ ws://localhost:8765                ║" -ForegroundColor White
Write-Host "║  🧠 Ollama LLM              │ http://localhost:11434             ║" -ForegroundColor White
Write-Host "╚══════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 Demo Features:" -ForegroundColor Yellow
Write-Host "   - No login required" -ForegroundColor White
Write-Host "   - Yellow banner shows 'Demo Mode Active'" -ForegroundColor White
Write-Host "   - Mr Happy AI assistant ready" -ForegroundColor White
Write-Host "   - Voice commands available (run wake word listener)" -ForegroundColor White
Write-Host ""

# Open browser
Write-Host "🔍 Opening browser..." -ForegroundColor Yellow
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "✅ AI Demo environment is ready!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Yellow
Write-Host "1. Explore the Activity Feed" -ForegroundColor White
Write-Host "2. Visit your 'Mr. Happy Digital CEO Board'" -ForegroundColor White
Write-Host "3. Chat with Mr Happy: http://localhost:8001/docs" -ForegroundColor White
Write-Host "4. Start voice assistant: python axzora-ai/mr-happy/wake_word.py" -ForegroundColor White
Write-Host "5. Try: python axzora.py junie (JetBrains AI coding agent)" -ForegroundColor White
Write-Host ""
Write-Host "🔧 For troubleshooting, check:" -ForegroundColor Yellow
Write-Host "   - Browser console (F12)" -ForegroundColor White
Write-Host "   - Backend logs in terminal" -ForegroundColor White
Write-Host "   - Ollama: ollama serve" -ForegroundColor White
Write-Host ""

Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")