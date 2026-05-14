@echo off
cd /d C:\Users\18341\Desktop\C-learning-platform
echo Cleaning Git history...
set FILTER_BRANCH_SQUELCH_WARNING=1
"C:\Program Files\Git\bin\git.exe" filter-branch --force --index-filter "git rm --cached --ignore-unmatch 部署平台到公网.md" --prune-empty -- --all
echo.
echo Pushing to GitHub...
"C:\Program Files\Git\bin\git.exe" push origin main --force
echo.
echo Done!
pause
