# Batch-Push Script für Chalkboards
# Pusht Dateien in Batches von maximal 10 MB

$maxBatchSizeMB = 10
$maxBatchSizeBytes = $maxBatchSizeMB * 1024 * 1024
$chalkboardsPath = "chalkboards_upload"

# Alle Dateien im chalkboards-Ordner finden
$allFiles = Get-ChildItem -Path $chalkboardsPath -Recurse -File | Sort-Object FullName

Write-Host "Gefunden: $($allFiles.Count) Dateien" -ForegroundColor Cyan

# Dateien in Batches aufteilen
$batches = @()
$currentBatch = @()
$currentBatchSize = 0

foreach ($file in $allFiles) {
    if ($currentBatchSize + $file.Length -gt $maxBatchSizeBytes -and $currentBatch.Count -gt 0) {
        # Batch voll, neuen starten
        $batches += ,@($currentBatch)
        $currentBatch = @()
        $currentBatchSize = 0
    }
    $currentBatch += $file
    $currentBatchSize += $file.Length
}

# Letzten Batch hinzufügen
if ($currentBatch.Count -gt 0) {
    $batches += ,@($currentBatch)
}

Write-Host "Aufgeteilt in $($batches.Count) Batches" -ForegroundColor Cyan
Write-Host ""

# Jeden Batch verarbeiten
$batchNum = 0
foreach ($batch in $batches) {
    $batchNum++
    $batchSizeMB = [math]::Round(($batch | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
    
    Write-Host "=== Batch $batchNum / $($batches.Count) ===" -ForegroundColor Yellow
    Write-Host "Dateien: $($batch.Count), Größe: $batchSizeMB MB" -ForegroundColor Gray
    
    # Dateien zum Staging hinzufügen
    foreach ($file in $batch) {
        $relativePath = $file.FullName.Substring((Get-Location).Path.Length + 1).Replace("\", "/")
        Write-Host "  Adding: $relativePath" -ForegroundColor DarkGray
        git add $relativePath
    }
    
    # Commit erstellen
    $firstFile = $batch[0].Name
    $lastFile = $batch[-1].Name
    $commitMsg = "chalkboards batch $batchNum`: $($batch.Count) files ($batchSizeMB MB)"
    
    git commit -m $commitMsg
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Fehler beim Commit! Abbruch." -ForegroundColor Red
        exit 1
    }
    
    # Push
    Write-Host "Pushing..." -ForegroundColor Gray
    git push
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Fehler beim Push! Abbruch." -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Batch $batchNum erfolgreich gepusht!" -ForegroundColor Green
    Write-Host ""
}

Write-Host "=== FERTIG ===" -ForegroundColor Green
Write-Host "Alle $($batches.Count) Batches wurden erfolgreich gepusht!" -ForegroundColor Green

