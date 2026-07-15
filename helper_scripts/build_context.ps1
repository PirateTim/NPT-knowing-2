<#
.SYNOPSIS
    Compiles source code into a single "Context Priming Manifest" for LLM ingestion.
.DESCRIPTION
    This script recursively scans the 'src' directory for code files (.py, .xml, .json).
    It reads their contents and appends them into a single text file, creating a 
    portable snapshot of the project's logic.
    
    CRITICAL SECURITY & SIZE BOUNDARIES:
    - This script is hardcoded to EXCLUDE environment files (.env), secret tokens, 
      and massive text repositories (logs, local_wiki, manuscript, output) to prevent 
      both context-window blowout and credential leakage.
.USAGE
    .\build_context.ps1
#>

# 1. Generate a dynamic filename based on the current date
$dateStr = Get-Date -Format "yyyy-MM-dd"
$outputFile = "project_context_manifest-$dateStr.txt"

# 2. Clear any existing file with the same name to prevent appending to stale data
Remove-Item -Path $outputFile -ErrorAction SilentlyContinue

# 3. Define the strict exclusion regex
# This acts as a firewall preventing the script from reading massive or sensitive folders.
# Even though the script is scoped to 'src', this ensures safety if the script is ever run from root.
$excludeRegex = '\\(\.venv|__pycache__|logs|local_wiki|manuscript|output)\\'

Write-Host "Building context manifest: $outputFile..."

# 4. The Extraction Pipeline
# - Get-ChildItem: Scans the "src" folder recursively.
# - Where-Object: Filters for specific code extensions AND explicitly blocks the exclusion regex.
Get-ChildItem -Path "src" -Recurse | 
    Where-Object { 
        $_.Extension -in '.py','.xml','.json','.txt','.md' -and 
        $_.FullName -notmatch $excludeRegex -and
        $_.Name -notmatch 'secret|token|\.env' # Double-check to exclude stray credential files
    } | 
    ForEach-Object {
        # A. Write the File Header (Helps the LLM understand where this code lives)
        $relativePath = $_.FullName.Replace((Get-Location).Path, '')
        Add-Content -Path $outputFile -Value "=== FILE_PATH: $relativePath ==="
        
        # B. Inject the Raw Content
        Add-Content -Path $outputFile -Value (Get-Content $_.FullName -Raw)
        
        # C. Write the File Footer (Provides a clean break for the LLM parser)
        Add-Content -Path $outputFile -Value "==================================================`n"
    }

Write-Host "Manifest compilation complete."