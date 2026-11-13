# End-to-end Windows installer check using a real runtime, package and Claude CLI.
# Everything installed/configured lives under a new temporary folder. Live is untouched.
[CmdletBinding()]
param([string]$ScratchRoot = (Join-Path ([IO.Path]::GetTempPath()) ('ableton-setup-check-' + [guid]::NewGuid().ToString('N'))))

$ErrorActionPreference = 'Stop'
$installer = Join-Path $PSScriptRoot 'install-claude-code.ps1'
$claude = (Get-Command claude -ErrorAction Stop).Source
$library = Join-Path $ScratchRoot 'Library With Spaces'
$root = Join-Path $ScratchRoot 'Private Runtime'
New-Item -ItemType Directory -Path (Join-Path $library 'Presets') -Force | Out-Null
$env:CLAUDE_CONFIG_DIR = Join-Path $ScratchRoot 'claude'
$env:ABLETONLIVEMCP_CONFIG = Join-Path $ScratchRoot 'bridge/bridge.json'
New-Item -ItemType Directory -Path $env:CLAUDE_CONFIG_DIR -Force | Out-Null

function Expect-Refusal {
    param([scriptblock]$Action, [string]$Message)
    $refused = $false
    try { & $Action } catch {
        if ($_.Exception.Message -notlike "*$Message*") { throw }
        $refused = $true
    }
    if (-not $refused) { throw "Expected refusal: $Message" }
}

# A test library cannot be loaded in Live. Supply process inventory at this boundary
# so the check can run while the owner's real Live process remains undisturbed.
function Get-Process { [pscustomobject]@{ ProcessName = 'Ableton Live test' } }
Expect-Refusal { & $installer -UserLibrary $library -InstallRoot $root -ClaudeCommand $claude } 'close Ableton Live'
function Get-Process { @() }
Expect-Refusal { & $installer -UserLibrary $ScratchRoot -InstallRoot $root -ClaudeCommand $claude } 'containing Presets'
if (Test-Path -LiteralPath $root) { throw 'Failed preflight created an installation.' }

& $installer -UserLibrary $library -InstallRoot $root -ClaudeCommand $claude
$configFile = Join-Path $env:CLAUDE_CONFIG_DIR '.claude.json'
$config = Get-Content -LiteralPath $configFile -Raw | ConvertFrom-Json
$server = Join-Path $root 'tools/zx-ableton-live-mcp/Scripts/abletonlivemcp.exe'
if ($config.mcpServers.abletonlive.command -ne $server) { throw 'Wrong registered command.' }
if (-not (Test-Path -LiteralPath $server)) { throw 'Server executable missing.' }
if (-not (Test-Path -LiteralPath (Join-Path $library 'Remote Scripts/AbletonLiveMCP/core.py'))) {
    throw 'Remote Script missing.'
}
$bridgeBefore = Get-Content -LiteralPath $env:ABLETONLIVEMCP_CONFIG -Raw
if (($bridgeBefore | ConvertFrom-Json).read_only -ne $true) { throw 'Fresh setup enabled writes.' }
$configBefore = Get-Content -LiteralPath $configFile -Raw
& $installer -UserLibrary $library -InstallRoot $root -ClaudeCommand $claude
if ((Get-Content -LiteralPath $env:ABLETONLIVEMCP_CONFIG -Raw) -ne $bridgeBefore) {
    throw 'Rerun changed the bridge policy or secret.'
}
if ((Get-Content -LiteralPath $configFile -Raw) -ne $configBefore) {
    throw 'Rerun changed an existing matching Claude entry.'
}
$config.mcpServers.abletonlive.command = 'D:/Music/another-server.exe'
$config | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $configFile -Encoding UTF8
$conflictBefore = Get-Content -LiteralPath $configFile -Raw
Expect-Refusal { & $installer -UserLibrary $library -InstallRoot $root -ClaudeCommand $claude } 'existing abletonlive entry'
if ((Get-Content -LiteralPath $configFile -Raw) -ne $conflictBefore) {
    throw 'Conflicting config was changed.'
}
Write-Host 'PASS: fresh install, rerun, Live guard, invalid library and preserved registration conflict.'
