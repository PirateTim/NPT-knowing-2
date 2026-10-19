<#
.SYNOPSIS
    NPT Fleet Directory Hierarchy Viewer

How to run:
    powershell -ExecutionPolicy Bypass -File helper_scripts/view_hierarchy.ps1

What it does:
    Renders an indented visual ASCII directory tree of the workspace structure.

Last run: Unknown
#>

# Record execution timestamp
try {
    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $file = $MyInvocation.MyCommand.Path
    if ($file -and (Test-Path $file)) {
        (Get-Content $file) -replace 'Last run:.*', "Last run: $now" | Set-Content $file
    }
} catch {}

# 1. Initialization: Clear the old map to ensure we don't append to stale data
$outputFile = "project_hierarchy.txt"
Remove-Item -Path $outputFile -ErrorAction SilentlyContinue

# 2. Set the anchor point for the directory walk
$rootPath = (Get-Location).Path

# 3. Define Exclusion Boundaries
# These regex patterns prevent the script from walking into massive, irrelevant directories
$excludePatterns = @(
    [regex]::Escape("src\react_agent\__pycache__"),
    [regex]::Escape(".venv")
)

function Walk-Directory ($currentDir, $indent = "") {
    # Fetch all items in the current directory (files and folders), silently ignoring access errors
    $items = Get-ChildItem -Path $currentDir -ErrorAction SilentlyContinue

    foreach ($item in $items) {
        # Check the current item against all registered exclusion boundaries
        $shouldSkip = $false
        foreach ($pattern in $excludePatterns) {
            if ($item.FullName -match $pattern) {
                $shouldSkip = $true
                break
            }
        }
        # If it matches an exclusion pattern, skip to the next item
        if ($shouldSkip) { continue }

        if ($item.PSIsContainer) {
            # It's a directory: Print with a [DIR] tag and a trailing slash
            Add-Content -Path $outputFile -Value "${indent}[DIR] $($item.Name)/"
            # Recursively walk into the directory, increasing the visual indentation
            Walk-Directory -currentDir $item.FullName -indent "${indent}    "
        } else {
            # It's a file: Print cleanly with a standard bullet
            Add-Content -Path $outputFile -Value "${indent}  - $($item.Name)"
        }
    }
}

# 4. Header Generation
# Using the -f format operator completely isolates strings from variable substitution parsing traps
Add-Content -Path $outputFile -Value "=== PROJECT ARCHITECTURE HIERARCHY ==="
Add-Content -Path $outputFile -Value ("Root: {0}" -f $rootPath)
Add-Content -Path $outputFile -Value "----------------------------------------"

# 5. Execute the Recursive Walk
Walk-Directory -currentDir $rootPath