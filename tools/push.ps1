# Windows PowerShell: daily commit + push
# Usage: powershell -ExecutionPolicy Bypass -File tools\push.ps1 "your message"
# Note: ASCII-only on purpose, so it parses on any Windows codepage.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$msg = if ($args.Count -gt 0) { $args[0] } else { "content update" }

if (-not (Test-Path .git)) {
    Write-Host "[x] no git repo here: run tools\setup.ps1 first"
    exit 1
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    python tools/build.py
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    py -3 tools/build.py
} else {
    Write-Host "[i] python not found: skip local build, GitHub Actions will build after push"
}

git add -A
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m $msg | Out-Null
    git push origin main
    Write-Host "[i] pushed to GitHub"
} else {
    Write-Host "[i] nothing to commit"
}
