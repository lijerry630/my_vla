# Windows PowerShell: first-time setup (connects to a repo that may already have commits)
# Usage: powershell -ExecutionPolicy Bypass -File tools\setup.ps1
# Note: ASCII-only on purpose, so it parses on any Windows codepage.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Test-Path "index.html")) {
    Write-Host "[x] index.html not found: run this script inside the site folder"
    exit 1
}

$cfg = Get-Content site.json -Raw | ConvertFrom-Json
$owner = $cfg.owner
$repo = $cfg.repo
$branch = if ($cfg.branch) { $cfg.branch } else { "main" }
if (-not $owner -or -not $repo) {
    Write-Host "[x] fill owner and repo in site.json first"
    exit 1
}

$url = if ($env:GIT_REMOTE_URL) { $env:GIT_REMOTE_URL } else { "https://github.com/$owner/$repo.git" }

if (-not (Test-Path .git)) {
    git init -b $branch | Out-Null
    Write-Host "[i] repository initialized on branch $branch"
}

git config user.name $owner
git config user.email "$owner@users.noreply.github.com"
git config core.quotepath false

git remote get-url origin *> $null
if ($LASTEXITCODE -ne 0) {
    git remote add origin $url
} else {
    git remote set-url origin $url
}
Write-Host "[i] remote: $url"

git fetch origin $branch --quiet
git rev-parse --verify --quiet HEAD *> $null
if ($LASTEXITCODE -ne 0) {
    git rev-parse --verify --quiet "origin/$branch" *> $null
    if ($LASTEXITCODE -eq 0) {
        git reset --soft "origin/$branch"
        Write-Host "[i] attached to existing remote history"
    }
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
    git commit -m "init: vla-notes site" | Out-Null
    Write-Host "[i] commit created"
} else {
    Write-Host "[i] nothing to commit"
}

git push -u origin $branch

Write-Host ""
Write-Host "Done: https://github.com/$owner/$repo"
Write-Host "Next: Settings - Pages - Deploy from a branch - branch $branch - folder / (root)"
Write-Host "Site: https://$owner.github.io/$repo/"
