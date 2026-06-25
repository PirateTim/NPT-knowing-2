# Compile file map and contents into an uncompromised context priming file
# Remove-Item -Path "project_context_manifest.txt" -ErrorAction SilentlyContinue
# build_context.ps1

# build_context.ps1
# Remove-Item -Path "project_context_manifest.txt" -ErrorAction SilentlyContinue

Get-ChildItem -Path "src" -Recurse | Where-Object { $_.Extension -in '.py','.xml','.json' -and $_.FullName -notmatch '\\(\.venv|__pycache__)\\'} | ForEach-Object {
    Add-Content -Path "project_context_manifest-2026-06-24-02.txt" -Value "=== FILE_PATH: $($_.FullName.Replace((Get-Location).Path, '')) ==="
    Add-Content -Path "project_context_manifest-2026-06-24-02.txt" -Value (Get-Content $_.FullName -Raw)
    Add-Content -Path "project_context_manifest-2026-06-24-02.txt" -Value "==================================================`n"
}