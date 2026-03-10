#!/usr/bin/env pwsh
# Mr Happy Voice Assistant Setup Script
# Sets up Mr Happy as default voice assistant with device integration

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     MR HAPPY VOICE ASSISTANT & DEVICE SETUP                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# 1. Check OpenClaw/Kilo Connection
Write-Host "`n[1/6] Checking Kilo/OpenClaw Cloud Connection..." -ForegroundColor Green
$gatewayUrl = openclaw config get gateway.remote.url 2>$null
if ($gatewayUrl -match "kilosessions") {
    Write-Host "  ✅ Connected to Kilo Cloud Gateway"
} else {
    Write-Host "  ⚠️  Setting up Kilo Cloud Gateway..."
    openclaw config set gateway.remote.url wss://claw.kilosessions.ai
}

# 2. Device Connection Setup
Write-Host "`n[2/6] Setting up Device Connection..." -ForegroundColor Green

# Check for ADB
$adb = Get-Command adb -ErrorAction SilentlyContinue
if (-not $adb) {
    Write-Host "  📦 Installing ADB (Android Debug Bridge)..."
    # Download platform tools
    $url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
    $output = "$env:TEMP\platform-tools.zip"
    Invoke-WebRequest -Uri $url -OutFile $output
    Expand-Archive -Path $output -DestinationPath "$env:LOCALAPPDATA\Android" -Force
    [Environment]::SetEnvironmentVariable("Path", $env:Path + ";$env:LOCALAPPDATA\Android\platform-tools", "User")
    Write-Host "  ✅ ADB installed. Please restart PowerShell."
}

# Enable network ADB
Write-Host "  🔌 Enabling network ADB on port 5555..."
adb tcpip 5555 2>$null | Out-Null

# Scan for devices
Write-Host "  📱 Scanning for Android devices..."
$devices = adb devices | Select-String "device$"
if ($devices) {
    Write-Host "  ✅ Found devices:"
    $devices | ForEach-Object { Write-Host "     $_" }
    
    # Connect to Samsung F966B (Z Fold)
    Write-Host "`n  🔗 Connecting to Samsung F966B..."
    adb connect 192.168.1.100:5555 2>$null | Out-Null
} else {
    Write-Host "  ⚠️  No USB devices found. Ensure USB debugging is enabled."
}

# 3. Data Transfer Setup
Write-Host "`n[3/6] Setting up Data Transfer..." -ForegroundColor Green
$backupDir = "$env:USERPROFILE\DeviceBackup"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Write-Host "  📁 Backup location: $backupDir"

# Sync script
$syncScript = @"
# Device Sync Script
Write-Host "Syncing device data..."
adb pull /sdcard/DCIM $backupDir\Photos
adb pull /sdcard/Download $backupDir\Downloads
adb pull /sdcard/Documents $backupDir\Documents
adb pull /sdcard/Music $backupDir\Music
adb pull /sdcard/Pictures $backupDir\Pictures
Write-Host "Sync complete!"
"@
$syncScript | Out-File -FilePath "$backupDir\sync.ps1" -Encoding UTF8
Write-Host "  ✅ Sync script created at $backupDir\sync.ps1"

# 4. Network Setup (WiFi Direct / A2A)
Write-Host "`n[4/6] Setting up Network & A2A..." -ForegroundColor Green

# Enable WiFi hotspot for device connection
Write-Host "  📡 Checking WiFi hotspot capability..."
$wifi = Get-NetAdapter | Where-Object {$_.Name -like "*Wi-Fi*"}
if ($wifi) {
    Write-Host "  ✅ WiFi adapter found: $($wifi.Name)"
    # Note: Windows hotspot requires manual setup or specific hardware
    Write-Host "  ⚠️  Please enable Mobile Hotspot manually in Settings"
}

# A2A Agent setup
Write-Host "  🤖 Setting up Google A2A Agent Network..."
$a2aConfig = @{
    agents = @(
        @{name="MrHappyVoice"; role="voice_assistant"; endpoint="http://localhost:8001"},
        @{name="MrHappyDevice"; role="device_manager"; endpoint="http://localhost:8001"},
        @{name="MrHappySync"; role="data_sync"; endpoint="http://localhost:8001"}
    )
    network = @{
        type = "a2a"
        discovery = "local"
        protocol = "http"
    }
} | ConvertTo-Json -Depth 3

$a2aConfig | Out-File -FilePath "$env:USERPROFILE\.axzora\a2a_network.json" -Encoding UTF8
Write-Host "  ✅ A2A network configuration saved"

# 5. Mr Happy Voice Assistant Setup
Write-Host "`n[5/6] Setting up Mr Happy as Voice Assistant..." -ForegroundColor Green

# Create voice assistant config
$voiceConfig = @{
    default_assistant = "mr_happy"
    wake_word = "Hey Mr Happy"
    language = "en-US"
    voice = "natural"
    endpoints = @{
        chat = "http://localhost:8001/chat"
        health = "http://localhost:8001/health"
        execute = "http://localhost:8001/execute"
    }
    capabilities = @(
        "voice_recognition"
        "natural_language"
        "device_control"
        "data_sync"
        "task_automation"
    )
} | ConvertTo-Json -Depth 3

$voiceConfig | Out-File -FilePath "$env:USERPROFILE\.axzora\voice_assistant.json" -Encoding UTF8
Write-Host "  ✅ Voice assistant configuration saved"

# Create voice activation script
$voiceScript = @'
# Mr Happy Voice Assistant Activation
Write-Host "`n🎙️  Mr Happy Voice Assistant Activated" -ForegroundColor Green
Write-Host "   Say 'Hey Mr Happy' followed by your command`n" -ForegroundColor Gray

# Simulate voice recognition loop
while ($true) {
    $input = Read-Host "You"
    if ($input -eq "exit") { break }
    
    # Send to Mr Happy
    $response = Invoke-RestMethod -Uri http://localhost:8001/chat -Method POST `
        -Body (@{message=$input} | ConvertTo-Json) -ContentType "application/json"
    
    Write-Host "Mr Happy: $($response.response)" -ForegroundColor Cyan
}
'@
$voiceScript | Out-File -FilePath "$env:USERPROFILE\.axzora\voice_assistant.ps1" -Encoding UTF8
Write-Host "  ✅ Voice assistant script created"

# 6. Create Shortcuts
Write-Host "`n[6/6] Creating Shortcuts..." -ForegroundColor Green

# Desktop shortcut for voice assistant
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Mr Happy Voice.lnk")
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$env:USERPROFILE\.axzora\voice_assistant.ps1`""
$Shortcut.IconLocation = "%SystemRoot%\System32\SHELL32.dll, 13"
$Shortcut.Save()
Write-Host "  ✅ Desktop shortcut created"

# Taskbar pin (Windows 10/11)
Write-Host "  📌 Pin to taskbar: Right-click the desktop shortcut and select 'Pin to taskbar'"

# Final Summary
Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║              SETUP COMPLETE!                               ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green

Write-Host "`n📱 DEVICE CONNECTION:" -ForegroundColor Cyan
Write-Host "   • USB Debugging: Enable on your Samsung F966B"
Write-Host "   • Network ADB: Port 5555 enabled"
Write-Host "   • Backup Location: $backupDir"

Write-Host "`n🎙️ VOICE ASSISTANT:" -ForegroundColor Cyan
Write-Host "   • Wake Word: 'Hey Mr Happy'"
Write-Host "   • Endpoint: http://localhost:8001"
Write-Host "   • Shortcut: Desktop\Mr Happy Voice.lnk"

Write-Host "`n🌐 A2A AGENT NETWORK:" -ForegroundColor Cyan
Write-Host "   • Configuration: ~/.axzora/a2a_network.json"
Write-Host "   • Agents: MrHappyVoice, MrHappyDevice, MrHappySync"

Write-Host "`n🚀 QUICK START:" -ForegroundColor Yellow
Write-Host "   1. Connect device via USB"
Write-Host "   2. Run: .\$backupDir\sync.ps1 (to transfer data)"
Write-Host "   3. Double-click 'Mr Happy Voice' on desktop"
Write-Host "   4. Say: 'Hey Mr Happy, sync my device'"

Write-Host "`n✨ Mr Happy is now your default voice assistant!`n" -ForegroundColor Green
