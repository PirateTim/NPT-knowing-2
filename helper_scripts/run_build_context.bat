@echo off
:: How to run:
::     helper_scripts\run_build_context.bat
::
:: What it does:
::     Windows batch wrapper that executes build_context.ps1 with execution policy bypass.
::
:: Last run: Unknown

echo Compiling project context manifest...

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_context.ps1"

echo.
echo Context priming file generated successfully.
pause