# Restart Ableton Live unattended: no crash-recovery dialog, wait until the bridge answers.
# Usage: powershell -File scripts\live_restart.ps1 [-Reinstall] [-Force]
# Basic Set is disposable (never saved), so a forced close loses nothing. Any other open Set
# (the owner's tracks) makes the script refuse; -Force overrides only on the owner's word.
param([switch]$Reinstall, [switch]$Force)
$ErrorActionPreference = 'Continue'
$repo = Split-Path -Parent $PSScriptRoot
$prefs = "$env:APPDATA\Ableton\Live 12.2\Preferences"
$exe = 'C:\ProgramData\Ableton\Live 12 Suite\Program\Ableton Live 12 Suite.exe'
$set = 'S:\AbletonMCP\projects\Basic Project\Basic.als'

$live = Get-Process | Where-Object { $_.Name -like 'Ableton Live*' }
if ($live) {
    $live | Select-Object Id, MainWindowTitle | Out-Host
    # Fail closed: an empty title (loading, modal dialog) could hide an owner Set.
    $other = $live | Where-Object { $_.MainWindowTitle -notmatch '^(Basic|Untitled)\*? - Ableton Live' }
    if ($other -and -not $Force) {
        Write-Error "Live has a non-Basic or unidentified Set open ('$($other.MainWindowTitle)'); not closing it"
        exit 4
    }
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
Start-Process -FilePath $exe -ArgumentList ('"{0}"' -f $set)
$up = $false
for ($i = 0; $i -lt 80; $i++) {
    Start-Sleep 3
    if ((Test-NetConnection 127.0.0.1 -Port 9877 -WarningAction SilentlyContinue).TcpTestSucceeded) { $up = $true; break }
}
Start-Sleep 30  # the bridge accepts early but drops the first calls while the Set loads
$opened = Get-Process | Where-Object { $_.Name -like 'Ableton Live*' -and $_.MainWindowTitle -like 'Basic*' }
if (-not $opened) {
    Start-Process -FilePath $set
    Start-Sleep 15
    $opened = Get-Process | Where-Object { $_.Name -like 'Ableton Live*' -and $_.MainWindowTitle -like 'Basic*' }
}
if (-not $opened) { Write-Error 'Basic did not reopen; do not build on Untitled'; exit 3 }
$opened | Select-Object Id, MainWindowTitle | Out-Host
"live up: $up"
if (-not $up) { exit 2 }
