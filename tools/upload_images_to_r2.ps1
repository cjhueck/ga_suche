# Upload-Skript: Vortragsbilder aus Steiner_GA/GA*/assets/ nach Cloudflare R2
# Organisiert als images/{GA-Nummer}/{dateiname} (z.B. images/GA094/img-0.png)
# Verwendung:
#   Alle:        powershell -ExecutionPolicy Bypass -File upload_images_to_r2.ps1
#   Auswahl:     powershell -ExecutionPolicy Bypass -File upload_images_to_r2.ps1 -FilterGA "GA028,GA211"
#   Fortsetzen:  powershell -ExecutionPolicy Bypass -File upload_images_to_r2.ps1 -StartFromGA "GA096"
#   Dry-Run:     powershell -ExecutionPolicy Bypass -File upload_images_to_r2.ps1 -DryRun

param(
    [string]$BucketName = "ga-pdf",
    [string]$SourceDir = "",
    [string]$FilterGA = "",
    [string]$StartFromGA = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

if (-not $SourceDir) {
    $SourceDir = Join-Path (Split-Path $PSScriptRoot -Parent) "Steiner_GA"
}

if (-not (Test-Path $SourceDir)) {
    Write-Host "FEHLER: Steiner_GA Ordner nicht gefunden: $SourceDir" -ForegroundColor Red
    exit 1
}

$contentTypes = @{
    ".png"  = "image/png"
    ".jpg"  = "image/jpeg"
    ".jpeg" = "image/jpeg"
    ".webp" = "image/webp"
    ".gif"  = "image/gif"
    ".svg"  = "image/svg+xml"
}

$filterList = @()
if ($FilterGA) {
    $filterList = $FilterGA.ToUpper() -split "," | ForEach-Object { $_.Trim() }
    Write-Host "Filter aktiv: $($filterList -join ', ')" -ForegroundColor Cyan
}

if ($StartFromGA) {
    $StartFromGA = $StartFromGA.ToUpper()
    Write-Host "Fortsetzen ab: $StartFromGA (fruehere GA-Baende werden uebersprungen)" -ForegroundColor Cyan
}

$gaFolders = Get-ChildItem -Path $SourceDir -Directory | Where-Object {
    $_.Name -match "^GA\d{1,3}[a-z]?"
} | Sort-Object Name

$uploaded = 0
$skipped = 0
$errors = 0
$totalFiles = 0
$startReached = if ($StartFromGA) { $false } else { $true }

foreach ($gaFolder in $gaFolders) {
    # GA-Nummer extrahieren (z.B. "GA094" aus "GA094-Theosophie...")
    if ($gaFolder.Name -match "^(GA\d{1,3}[a-z]?)") {
        $gaNumber = $Matches[1].ToUpper()
    } else {
        continue
    }

    # StartFromGA: alles vor dem Startpunkt ueberspringen
    if (-not $startReached) {
        if ($gaNumber -eq $StartFromGA) {
            $startReached = $true
        } else {
            continue
        }
    }

    # Filter anwenden
    if ($filterList.Count -gt 0 -and $gaNumber -notin $filterList) {
        continue
    }

    $assetsDir = Join-Path $gaFolder.FullName "assets"
    if (-not (Test-Path $assetsDir)) {
        continue
    }

    $allImageFiles = Get-ChildItem -Path $assetsDir -File | Where-Object {
        $contentTypes.ContainsKey($_.Extension.ToLower())
    }

    if ($allImageFiles.Count -eq 0) {
        continue
    }

    # Pro Bildname nur ein Format hochladen (Prioritaet: png > jpeg > jpg > webp > gif > svg)
    $extPriority = @{ ".png" = 0; ".jpeg" = 1; ".jpg" = 2; ".webp" = 3; ".gif" = 4; ".svg" = 5 }
    $bestPerName = @{}
    foreach ($f in $allImageFiles) {
        $baseName = [System.IO.Path]::GetFileNameWithoutExtension($f.Name)
        $prio = $extPriority[$f.Extension.ToLower()]
        if ($null -eq $prio) { $prio = 99 }
        if (-not $bestPerName.ContainsKey($baseName) -or $prio -lt $bestPerName[$baseName].Prio) {
            $bestPerName[$baseName] = @{ File = $f; Prio = $prio }
        }
    }
    $imageFiles = $bestPerName.Values | ForEach-Object { $_.File } | Sort-Object Name
    $dupesSkipped = $allImageFiles.Count - $imageFiles.Count

    Write-Host "`n--- $gaNumber ($($imageFiles.Count) Bilder, $dupesSkipped Duplikate uebersprungen) ---" -ForegroundColor Yellow

    foreach ($img in $imageFiles) {
        $totalFiles++
        $ext = $img.Extension.ToLower()
        $ct = $contentTypes[$ext]
        $targetKey = "images/$gaNumber/$($img.Name)"

        if ($DryRun) {
            Write-Host "  [DRY-RUN] $($img.Name) -> $targetKey"
            $uploaded++
            continue
        }

        try {
            Write-Host "  $($img.Name) -> $targetKey ..." -NoNewline
            npx wrangler r2 object put "${BucketName}/${targetKey}" --file="$($img.FullName)" --content-type="$ct" --remote 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host " OK" -ForegroundColor Green
                $uploaded++
            } else {
                Write-Host " FEHLER (exit $LASTEXITCODE)" -ForegroundColor Red
                $errors++
            }
        } catch {
            Write-Host " FEHLER: $_" -ForegroundColor Red
            $errors++
        }
    }
}

Write-Host "`n========================================="
Write-Host "Ergebnis: $uploaded hochgeladen, $skipped Duplikate uebersprungen, $errors Fehler (von $totalFiles Dateien)"
Write-Host "========================================="
