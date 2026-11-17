@echo off
title CareerLens Cloud Data Sync
echo ==============================================
echo   CareerLens - Sync Live Cloud Data to Local
echo ==============================================
echo.
python sync_userdata.py %*
echo.
echo Press any key to close this window...
pause >nul
