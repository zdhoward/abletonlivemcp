# Restart Ableton Live unattended: no crash-recovery dialog, wait until the bridge answers.
# Usage: powershell -File scripts\live_restart.ps1 [-Reinstall]
# Basic Set is disposable (never saved), so a forced close loses nothing.
param([switch]$Reinstall)
$ErrorActionPreference = 'Continue'
$repo = Split-Path -Parent $PSScriptRoot
$prefs = "$env:APPDATA\Ableton\Live 12.2\Preferences"
$exe = 'C:\ProgramData\Ableton\Live 12 Suite\Program\Ableton Live 12 Suite.exe'
$set = 'S:\AbletonMCP\projects\Basic Project\Basic.als'

$live = Get-Process | Where-Object { $_.Name -like 'Ableton Live*' }
if ($live) {
    $live | ForEach-Object { [void]$_.CloseMainWindow() }
    Start-Sleep 4
    Get-Process | Where-Object { $_.Name -like 'Ableton Live*' } | Stop-Process -Force
    Start-Sleep 3
}
# Without these files Live sees no unclean shutdown and shows no recovery prompt.
foreach ($f in 'CrashDetection.cfg', 'CrashRecoveryInfo.cfg') { Remove-Item "$prefs\$f" -Force -ErrorAction SilentlyContinue }
foreach ($d in 'Crash', 'Undo') { Remove-Item "$prefs\$d\*" -Recurse -Force -ErrorAction SilentlyContinue }

if ($Reinstall) {
    & "$repo\.venv\Scripts\python.exe" -m abletonlivemcp.install 'D:\Beatz\DAWs\Ableton 12\User Library' | Select-Object -Last 1
}
Start-Process $exe $set
$up = $false
for ($i = 0; $i -lt 80; $i++) {
    Start-Sleep 3
    if ((Test-NetConnection 127.0.0.1 -Port 9877 -WarningAction SilentlyContinue).TcpTestSucceeded) { $up = $true; break }
}
Start-Sleep 30  # the bridge accepts early but drops the first calls while the Set loads
"live up: $up"
if (-not $up) { exit 2 }
