$ErrorActionPreference = "Stop"
Set-Location "C:\Users\chuec\OneDrive\GitHub\ga_suche"

$allFiles = Get-ChildItem -Path "chalkboards" -Recurse -File | Select-Object -ExpandProperty FullName
$batchSize = 30
$totalFiles = $allFiles.Count
$batches = [math]::Ceiling($totalFiles / $batchSize)

Write-Host "Starte Upload von $totalFiles Dateien in $batches Batches..." -ForegroundColor Green

for ($i = 0; $i -lt $batches; $i++) {
    $start = $i * $batchSize
    $end = [math]::Min(($i + 1) * $batchSize - 1, $totalFiles - 1)
    $batchFiles = $allFiles[$start..$end]
    
    Write-Host "`nBatch $($i + 1)/$batches (Dateien $($start + 1) bis $($end + 1))..." -ForegroundColor Cyan
    
    foreach ($file in $batchFiles) {
        $relativePath = $file.Replace("C:\Users\chuec\OneDrive\GitHub\ga_suche\", "")
        git add $relativePath 2>$null
    }
    
    git commit -m "Add chalkboards batch $($i + 1)/$batches" 2>$null
    
    Write-Host "Pushing batch $($i + 1)..." -ForegroundColor Yellow
    git push 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Fehler bei Batch $($i + 1)! Versuche erneut..." -ForegroundColor Red
        Start-Sleep -Seconds 5
        git push 2>&1
    }
    
    Write-Host "Batch $($i + 1) erfolgreich!" -ForegroundColor Green
}

Write-Host "`nAlle $batches Batches erfolgreich hochgeladen!" -ForegroundColor Green

