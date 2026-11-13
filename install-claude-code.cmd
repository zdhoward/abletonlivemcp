@echo off
setlocal
title AbletonLiveMCP setup for Claude Code
echo Installing AbletonLiveMCP for Claude Code...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $setupFile = Join-Path ([IO.Path]::GetTempPath()) ('abletonlivemcp-' + [guid]::NewGuid().ToString('N') + '.ps1'); try { Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/zdhoward/abletonlivemcp/main/scripts/install-claude-code.ps1' -OutFile $setupFile; & $setupFile; if ($LASTEXITCODE -ne 0) { exit 1 } } catch { Write-Host ('Setup failed: ' + $_.Exception.Message) -ForegroundColor Red; exit 1 } finally { Remove-Item -LiteralPath $setupFile -ErrorAction SilentlyContinue }"
set "setupExit=%ERRORLEVEL%"
echo.
pause
exit /b %setupExit%
