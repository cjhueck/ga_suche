# Export Page Markers für ALLE GAs
# Dieses Script exportiert Seitenzahlen für alle verfügbaren PDFs

$ErrorActionPreference = "Continue"
Set-Location "c:\Users\chuec\OneDrive\GitHub\ga_suche"

# Alle GA-Nummern aus PDFs extrahieren
$pdfDir = "c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf"
$gaNumbers = Get-ChildItem -Path $pdfDir -Filter "*.pdf" | ForEach-Object {
    if ($_.Name -match 'GA\s*(\d+)') {
        [int]$Matches[1]
    }
} | Sort-Object -Unique

Write-Host "Gefunden: $($gaNumbers.Count) GA-Nummern mit PDFs" -ForegroundColor Green
Write-Host ""

# Bereits vorhandene Marker laden
$existingMarkers = @()
if (Test-Path "page-markers.json") {
    $pm = Get-Content "page-markers.json" | ConvertFrom-Json
    $existingMarkers = $pm.PSObject.Properties.Name | Where-Object { $_ -match '^GA\d+$' } | ForEach-Object {
        if ($_ -match 'GA(\d+)') { [int]$Matches[1] }
    }
}
Write-Host "Bereits vorhanden: $($existingMarkers.Count) GA-Nummern" -ForegroundColor Yellow

# Fehlende GAs ermitteln
$missingGAs = $gaNumbers | Where-Object { $_ -notin $existingMarkers }
Write-Host "Fehlend: $($missingGAs.Count) GA-Nummern" -ForegroundColor Cyan
Write-Host ""

# Export in Batches von 5
$batchSize = 5
$totalBatches = [Math]::Ceiling($missingGAs.Count / $batchSize)

for ($i = 0; $i -lt $missingGAs.Count; $i += $batchSize) {
    $batch = $missingGAs[$i..([Math]::Min($i + $batchSize - 1, $missingGAs.Count - 1))]
    $batchNum = [Math]::Floor($i / $batchSize) + 1
    
    $gaArgs = $batch | ForEach-Object { "GA$($_.ToString().PadLeft(3, '0'))" }
    $gaArgsStr = $gaArgs -join " "
    
    Write-Host "===== Batch $batchNum/$totalBatches =====" -ForegroundColor Magenta
    Write-Host "Exportiere: $gaArgsStr" -ForegroundColor White
    
    # Python Script ausführen
    python export_page_markers_v2.py $gaArgs 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Warnung: Fehler bei Batch $batchNum" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

Write-Host ""
Write-Host "===== EXPORT ABGESCHLOSSEN =====" -ForegroundColor Green

# Statistik
$pm = Get-Content "page-markers.json" | ConvertFrom-Json
$finalCount = ($pm.PSObject.Properties.Name | Where-Object { $_ -match '^GA\d+$' }).Count
Write-Host "Gesamt: $finalCount GA-Nummern in page-markers.json" -ForegroundColor Green





















