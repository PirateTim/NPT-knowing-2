@echo off
:: ==============================================================================
:: NPT Fleet Utility: Run Hierarchy Mapper
:: Description: A simple wrapper to execute the view_hierarchy.ps1 script.
:: Why use this?: It automatically bypasses Windows PowerShell execution policies 
:: which normally block unsigned local scripts from running.
:: .\helper_scripts\run_view_heirarchy.bat
:: cls & cd /d "c:\Users\timot\NPT-knowing-2" & "c:\Users\timot\NPT-knowing-2\helper_scripts\run_view_heirarchy.bat
:: ==============================================================================

echo Compiling project context manifest...

:: Execute the PowerShell script located in the exact same directory as this batch file (%~dp0)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0view_hierarchy.ps1"

echo.
echo Context priming file generated successfully.
pause