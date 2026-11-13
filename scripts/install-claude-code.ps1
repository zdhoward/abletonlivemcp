# Windows setup for Claude Code. Double-click install-claude-code.cmd, or run:
# powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install-claude-code.ps1
# -UserLibrary and -InstallRoot support unattended setup and isolated verification.
[CmdletBinding()]
param(
    [string]$UserLibrary,
    [string]$InstallRoot = (Join-Path $env:LOCALAPPDATA 'AbletonLiveMCP'),
    [string]$ClaudeCommand
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Invoke-Checked {
    param([string]$Command, [string[]]$Arguments)
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed (exit $LASTEXITCODE): $Command. Fix the error above and rerun setup."
    }
}

function Select-UserLibrary {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = 'Select the User Library shown in Ableton Live Settings > Library.'
    $dialog.ShowNewFolderButton = $false
    $defaultLibrary = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'Ableton/User Library'
    if (Test-Path -LiteralPath $defaultLibrary -PathType Container) {
        $dialog.SelectedPath = $defaultLibrary
    }
    try {
        if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
            throw 'Setup cancelled. No changes were made.'
        }
        return $dialog.SelectedPath
    } finally {
        $dialog.Dispose()
    }
}

function Assert-LiveClosed {
    $live = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like 'Ableton Live*' }
    if ($live) {
        throw 'Save your Set and close Ableton Live, then rerun setup.'
    }
}

if (-not $ClaudeCommand) {
    $claude = Get-Command claude -ErrorAction SilentlyContinue
    if ($claude) {
        $ClaudeCommand = $claude.Source
    } else {
        $nativeClaude = Join-Path $env:USERPROFILE '.local/bin/claude.exe'
        if (Test-Path -LiteralPath $nativeClaude -PathType Leaf) {
            $ClaudeCommand = $nativeClaude
        } else {
            throw 'Install Claude Code first: https://code.claude.com/docs/en/setup . Then rerun this installer.'
        }
    }
}
if (-not (Test-Path -LiteralPath $ClaudeCommand -PathType Leaf)) {
    throw 'The Claude Code command could not be found.'
}

# Live must be closed before its Remote Script is replaced. Do not terminate a Set.
Assert-LiveClosed
if (-not $UserLibrary) {
    $UserLibrary = Select-UserLibrary
}
if (-not (Test-Path -LiteralPath (Join-Path $UserLibrary 'Presets') -PathType Container)) {
    throw 'Select your Ableton User Library (the folder containing Presets), then rerun setup.'
}
$UserLibrary = (Resolve-Path -LiteralPath $UserLibrary).Path
$InstallRoot = [IO.Path]::GetFullPath($InstallRoot)
$server = Join-Path $InstallRoot 'tools/zx-ableton-live-mcp/Scripts/abletonlivemcp.exe'

# Use Claude's own configuration writer. For a rerun, leave an identical user entry
# alone; refuse to overwrite a manually configured entry or unrelated command.
$configDirectory = $env:CLAUDE_CONFIG_DIR
$claudeConfig = if ($configDirectory) {
    Join-Path $configDirectory '.claude.json'
} else {
    Join-Path $env:USERPROFILE '.claude.json'
}
$registered = $false
if (Test-Path -LiteralPath $claudeConfig -PathType Leaf) {
    $config = Get-Content -LiteralPath $claudeConfig -Raw | ConvertFrom-Json
    if ($config.PSObject.Properties['mcpServers'] -and $config.mcpServers -and
        $config.mcpServers.PSObject.Properties['abletonlive']) {
        $entry = $config.mcpServers.abletonlive
        if (-not $entry.PSObject.Properties['command'] -or
            $entry.command.Replace('/', '\') -ne $server.Replace('/', '\') -or
            ($entry.PSObject.Properties['type'] -and $entry.type -ne 'stdio') -or
            ($entry.PSObject.Properties['args'] -and @($entry.args).Count -gt 0) -or
            ($entry.PSObject.Properties['env'] -and @($entry.env.PSObject.Properties).Count -gt 0)) {
            throw 'An existing abletonlive entry uses a different setup. It was preserved. See docs/setup.md#one-click-installer.'
        }
        $registered = $true
    }
}

Write-Host '1/3 Installing a private Python runtime and AbletonLiveMCP...'
$bootstrap = Join-Path $InstallRoot 'bootstrap'
New-Item -ItemType Directory -Path $bootstrap -Force | Out-Null
$uv = Join-Path $bootstrap 'uv.exe'
if (-not (Test-Path -LiteralPath $uv -PathType Leaf)) {
    # Pin the bootstrap archive and verify its SHA-256 before executing it.
    # uv installs managed Python without adding Python or uv to the user's PATH.
    $archive = Join-Path $bootstrap ('uv-' + [guid]::NewGuid().ToString('N') + '.zip')
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/astral-sh/uv/releases/download/0.13.8/uv-x86_64-pc-windows-msvc.zip' -OutFile $archive
        $expected = '529e78a9cec6cd7e3e014f7ecd8bda0c113969d4ed0f2efeedb85c30943325b8'
        if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $expected) {
            throw 'The runtime download failed its integrity check. Rerun setup to download it again.'
        }
        Expand-Archive -LiteralPath $archive -DestinationPath $bootstrap -Force
    } finally {
        Remove-Item -LiteralPath $archive -ErrorAction SilentlyContinue
    }
}

# These variables affect only this installer process, never the user's saved environment.
$env:UV_TOOL_DIR = Join-Path $InstallRoot 'tools'
$env:UV_TOOL_BIN_DIR = Join-Path $InstallRoot 'bin'
$env:UV_PYTHON_INSTALL_DIR = Join-Path $InstallRoot 'python'
Invoke-Checked $uv @('tool', 'install', '--no-config', '--managed-python', '--python', '3.13', '--upgrade', 'zx-ableton-live-mcp')

Write-Host '2/3 Installing the Ableton Remote Script...'
Assert-LiveClosed
$scriptInstaller = Join-Path $InstallRoot 'tools/zx-ableton-live-mcp/Scripts/abletonlivemcp-install.exe'
Invoke-Checked $scriptInstaller @($UserLibrary)

Write-Host '3/3 Connecting Claude Code...'
if (-not $registered) {
    Invoke-Checked $ClaudeCommand @('mcp', 'add', '--transport', 'stdio', '--scope', 'user', 'abletonlive', '--', $server)
}

Write-Host ''
Write-Host 'Installed! Finish in Ableton Live:' -ForegroundColor Green
Write-Host '  Open Settings > Link, Tempo & MIDI > Control Surface.'
Write-Host '  Select AbletonLiveMCP in a free slot.'
Write-Host 'Then start a new Claude Code session and ask:'
Write-Host '  Check Ableton with live_hello and tell me the tempo of my Set.'
Write-Host 'Writes are disabled by default. See docs/setup.md#enable-writes to enable editing.'
