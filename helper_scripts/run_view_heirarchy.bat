@echo off
:: How to run:
::     helper_scripts\run_view_heirarchy.bat
::
:: What it does:
::     Windows batch wrapper that executes view_hierarchy.ps1 with execution policy bypass.
::
:: Last run: Unknown

echo Compiling project context manifest...

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0view_hierarchy.ps1"

echo.
echo Context priming file generated successfully.
pause