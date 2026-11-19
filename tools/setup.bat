@echo off
setlocal
cd /d "%~dp0.."

rem ==== edit these three lines if the repository name changes (ASCII only) ====
set "OWNER=lijerry630"
set "REPO=my_vla"
set "BRANCH=main"
rem =======================================================================

if not exist index.html (
  echo [x] index.html not found: run this script inside the site folder
  exit /b 1
)

if not exist .git (
  git init -b %BRANCH%
  echo [i] git repository initialized on branch %BRANCH%
)

git config user.name %OWNER%
git config user.email %OWNER%@users.noreply.github.com
git config core.quotepath false

git remote get-url origin >nul 2>nul
if errorlevel 1 (
  git remote add origin https://github.com/%OWNER%/%REPO%.git
) else (
  git remote set-url origin https://github.com/%OWNER%/%REPO%.git
)
echo [i] remote: https://github.com/%OWNER%/%REPO%.git

git fetch origin %BRANCH% --quiet
git rev-parse --verify --quiet HEAD >nul 2>nul
if errorlevel 1 (
  git rev-parse --verify --quiet origin/%BRANCH% >nul 2>nul
  if not errorlevel 1 (
    git reset --soft origin/%BRANCH%
    echo [i] attached to existing remote history
  )
)

where python >nul 2>nul
if not errorlevel 1 (
  python tools\build.py
) else (
  echo [i] python not found: skip local build, GitHub Actions will build after push
)

git add -A
git commit -m "init: vla-notes site"
git push -u origin %BRANCH%

echo.
echo Done: https://github.com/%OWNER%/%REPO%
echo Next: Settings - Pages - Deploy from a branch - branch %BRANCH% - folder / (root)
echo Site: https://%OWNER%.github.io/%REPO%/
