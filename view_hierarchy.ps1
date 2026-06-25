# Clear or create the output file
$outputFile = "project_hierarchy.txt"
Remove-Item -Path $outputFile -ErrorAction SilentlyContinue

# Define the root path (current directory)
$rootPath = (Get-Location).Path

# Strict exclusion patterns for both python cache and virtual environments
$excludePatterns = @(
    [regex]::Escape("src\react_agent\__pycache__"),
    [regex]::Escape(".venv")
)

function Walk-Directory ($currentDir, $indent = "") {
    # Fetch all items in the current directory (files and folders)
    $items = Get-ChildItem -Path $currentDir -ErrorAction SilentlyContinue

    foreach ($item in $items) {
        # Check against all registered exclusion boundaries
        $shouldSkip = $false
        foreach ($pattern in $excludePatterns) {
            if ($item.FullName -match $pattern) {
                $shouldSkip = $true
                break
            }
        }
        if ($shouldSkip) { continue }

        if ($item.PSIsContainer) {
            # It's a directory: Print with a trailing slash to denote a folder
            Add-Content -Path $outputFile -Value "${indent}[DIR] $($item.Name)/"
            # Recursively walk into the directory, adding indentation for depth
            Walk-Directory -currentDir $item.FullName -indent "${indent}    "
        } else {
            # It's a file: Print cleanly
            Add-Content -Path $outputFile -Value "${indent}  - $($item.Name)"
        }
    }
}

# Initialize the walk at the root of your project
# Using -f format operator completely isolates strings from variable substitution parsing traps
Add-Content -Path $outputFile -Value "=== PROJECT ARCHITECTURE HIERARCHY ==="
Add-Content -Path $outputFile -Value ("Root: {0}" -f $rootPath)
Add-Content -Path $outputFile -Value "----------------------------------------"
Walk-Directory -currentDir $rootPath