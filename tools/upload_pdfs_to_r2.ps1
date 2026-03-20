# Upload-Skript: PDFs aus "GA fvn pdf" nach Cloudflare R2
# Normalisiert Dateinamen zu lowercase (GA028.pdf -> ga028.pdf)
# Verwendung: powershell -ExecutionPolicy Bypass -File upload_pdfs_to_r2.ps1

param(
    [string]$BucketName = "ga-pdf",
    [string]$SourceDir = "C:\Users\chuec\OneDrive\Anthroposophie\GA fvn pdf",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# Nur Haupt-GA-PDFs (GAxxxx.pdf / gaxxxx.pdf), keine Einzelvortraege oder Sonderdateien
$files = Get-ChildItem -Path $SourceDir -File -Filter "*.pdf" | Where-Object {
    $_.Name -match '^(?i)ga\d{1,3}[a-z]?\.pdf$'
}

Write-Host "Gefunden: $($files.Count) GA-PDFs in $SourceDir"
Write-Host ""

$uploaded = 0
$skipped = 0
$errors = 0

foreach ($file in $files) {
    # Dateiname normalisieren: lowercase
    $targetName = $file.Name.ToLower()

    if ($DryRun) {
        Write-Host "[DRY-RUN] $($file.Name) -> $targetName"
        $uploaded++
        continue
    }

    try {
        Write-Host "Uploading: $($file.Name) -> $targetName ..." -NoNewline
        npx wrangler r2 object put "${BucketName}/${targetName}" --file="$($file.FullName)" --content-type="application/pdf" --remote 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host " OK"
            $uploaded++
        } else {
            Write-Host " FEHLER (exit code $LASTEXITCODE)"
            $errors++
        }
    } catch {
        Write-Host " FEHLER: $_"
        $errors++
    }
}

Write-Host ""
Write-Host "========================================="
Write-Host "Ergebnis: $uploaded hochgeladen, $skipped uebersprungen, $errors Fehler"
Write-Host "========================================="
