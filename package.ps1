# Skill Package Script for 日志保存与分析
# Usage: .\package.ps1

$SkillName = "日志保存与分析"
$SourceDir = $PSScriptRoot
$OutputDir = Join-Path $SourceDir "dist"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ZipName = "$Timestamp.zip"
$ZipPath = Join-Path $OutputDir $ZipName

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

Write-Host "========================================"
Write-Host "Skill Package Tool"
Write-Host "========================================"
Write-Host ""

Write-Host "Files to package:"
$Files = Get-ChildItem -Path $SourceDir -Recurse -File | Where-Object { $_.Name -ne "package.ps1" -and $_.Name -notlike "*.zip" }
foreach ($file in $Files) {
    $RelativePath = $file.FullName.Replace($SourceDir + "\", "")
    Write-Host "  - $RelativePath"
}

Write-Host ""
Write-Host "Packaging..."

# Create zip archive (exclude package.ps1 and existing zip files)
Compress-Archive -Path $SourceDir\* -DestinationPath $ZipPath -Exclude "package.ps1","*.zip" -Force

if (Test-Path $ZipPath) {
    $FileSize = (Get-Item $ZipPath).Length / 1KB
    Write-Host ""
    Write-Host "Package complete!"
    Write-Host "Location: $ZipPath"
    Write-Host "Size: $([math]::Round($FileSize, 2)) KB"
    Write-Host ""

    # Calculate compression ratio
    $OriginalSize = ($Files | Measure-Object -Property Length -Sum).Sum / 1KB
    $Ratio = [math]::Round(($FileSize / $OriginalSize) * 100, 1)
    Write-Host "Original size: $([math]::Round($OriginalSize, 2)) KB"
    Write-Host "Compression: $Ratio%"
} else {
    Write-Host "Package failed!"
}

Write-Host ""
Write-Host "========================================"
