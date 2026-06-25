@echo off
echo Compiling project context manifest...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0view_hierarchy.ps1"
echo.
echo Context priming file generated successfully.
pause