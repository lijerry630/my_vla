@echo off
setlocal
cd /d "%~dp0.."

set "BRANCH=main"
set "MSG=%~1"
if "%MSG%"=="" set "MSG=content update"

where python >nul 2>nul
if not errorlevel 1 (
  python tools\build.py
) else (
  echo [i] python not found: skip local build, GitHub Actions will build after push
)

git add -A
git diff --cached --quiet
if errorlevel 1 (
  git commit -m "%MSG%"
  git push origin %BRANCH%
  echo [i] pushed to GitHub
) else (
  echo [i] nothing to commit
)
