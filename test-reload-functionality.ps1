# Test-Skript für Reload-Funktionalität
# Überprüft ob der Reload-Endpoint funktioniert

param(
    [string]$ServerUrl = "http://localhost:3003"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test: Reload-Funktionalität" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Prüfe ob Server läuft
Write-Host "[1/4] Prüfe Server-Status..." -ForegroundColor Yellow
try {
    $statusResponse = Invoke-RestMethod -Uri "$ServerUrl/api/debug/status" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✓ Server läuft auf $ServerUrl" -ForegroundColor Green
    Write-Host "   Status: $($statusResponse | ConvertTo-Json -Compress)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Server nicht erreichbar auf $ServerUrl" -ForegroundColor Red
    Write-Host "   Bitte starte den Server zuerst:" -ForegroundColor Yellow
    Write-Host "   .\server-control.ps1 start" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# 2. Hole aktuelle Anzahl von Lectures VOR Reload
Write-Host "[2/4] Hole aktuelle Anzahl von Lectures..." -ForegroundColor Yellow
try {
    $beforeResponse = Invoke-RestMethod -Uri "$ServerUrl/api/full-lectures" -Method GET -TimeoutSec 5
    $beforeCount = ($beforeResponse | ConvertTo-Json | ConvertFrom-Json | Measure-Object).Count
    Write-Host "✓ Aktuelle Anzahl: $beforeCount Lectures" -ForegroundColor Green
    
    # Prüfe ob GA012 vorhanden ist
    $ga012Found = $false
    foreach ($key in $beforeResponse.PSObject.Properties.Name) {
        if ($key -like "GA012/*") {
            $ga012Found = $true
            Write-Host "✓ GA012 gefunden: $key" -ForegroundColor Green
            break
        }
    }
    if (-not $ga012Found) {
        Write-Host "⚠️ GA012 nicht in aktuellen Lectures gefunden" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Konnte Lectures nicht abrufen: $_" -ForegroundColor Yellow
    $beforeCount = 0
}

Write-Host ""

# 3. Teste Reload-Endpoint
Write-Host "[3/4] Teste Reload-Endpoint..." -ForegroundColor Yellow
try {
    $reloadResponse = Invoke-RestMethod -Uri "$ServerUrl/api/reload-lectures" -Method POST -ContentType "application/json" -TimeoutSec 60
    if ($reloadResponse.success) {
        Write-Host "✓ Reload erfolgreich!" -ForegroundColor Green
        Write-Host "   Lectures geladen: $($reloadResponse.lecturesLoaded)" -ForegroundColor Cyan
        Write-Host "   Beispiel-Lectures:" -ForegroundColor Gray
        foreach ($lectureId in $reloadResponse.lectures) {
            Write-Host "     - $lectureId" -ForegroundColor Gray
        }
    } else {
        Write-Host "❌ Reload fehlgeschlagen" -ForegroundColor Red
        Write-Host ($reloadResponse | ConvertTo-Json) -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Fehler beim Reload: $_" -ForegroundColor Red
    Write-Host "   Response: $($_.Exception.Response)" -ForegroundColor Gray
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "   Body: $responseBody" -ForegroundColor Gray
    }
    exit 1
}

Write-Host ""

# 4. Prüfe ob GA012 nach Reload vorhanden ist
Write-Host "[4/4] Prüfe GA012 nach Reload..." -ForegroundColor Yellow
try {
    $afterResponse = Invoke-RestMethod -Uri "$ServerUrl/api/full-lectures" -Method GET -TimeoutSec 5
    $afterCount = ($afterResponse | ConvertTo-Json | ConvertFrom-Json | Measure-Object).Count
    Write-Host "✓ Neue Anzahl: $afterCount Lectures" -ForegroundColor Green
    
    # Prüfe speziell GA012
    $ga012Lectures = @()
    foreach ($key in $afterResponse.PSObject.Properties.Name) {
        if ($key -like "GA012/*") {
            $ga012Lectures += $key
        }
    }
    
    if ($ga012Lectures.Count -gt 0) {
        Write-Host "✓ GA012 Lectures gefunden:" -ForegroundColor Green
        foreach ($lectureId in $ga012Lectures) {
            Write-Host "   - $lectureId" -ForegroundColor Cyan
            # Prüfe ob Seitenzahlen vorhanden sind
            $lecture = $afterResponse.$lectureId
            if ($lecture.paragraphs) {
                $hasPageNumbers = $false
                foreach ($para in $lecture.paragraphs) {
                    $content = $para.content -or $para.text -or ""
                    if ($content -match '\|\d+\|') {
                        $hasPageNumbers = $true
                        break
                    }
                }
                if ($hasPageNumbers) {
                    Write-Host "     ✓ Seitenzahlen gefunden" -ForegroundColor Green
                } else {
                    Write-Host "     ⚠️ Keine Seitenzahlen gefunden" -ForegroundColor Yellow
                }
            }
        }
    } else {
        Write-Host "⚠️ Keine GA012 Lectures gefunden" -ForegroundColor Yellow
    }
    
    # Vergleich
    if ($beforeCount -ne $afterCount) {
        Write-Host "⚠️ Anzahl hat sich geändert: $beforeCount → $afterCount" -ForegroundColor Yellow
    } else {
        Write-Host "✓ Anzahl unverändert (erwartet)" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️ Konnte Lectures nach Reload nicht abrufen: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ Test abgeschlossen!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Nächste Schritte:" -ForegroundColor Cyan
Write-Host "1. Prüfe die Seitenzahlen in GA012 online" -ForegroundColor White
Write-Host "2. Falls nicht aktualisiert, führe aus: .\deploy-updates.ps1" -ForegroundColor White
Write-Host "3. Oder starte den Server neu: .\server-control.ps1 restart" -ForegroundColor White

