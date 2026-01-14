# Deployment-Skript: Pullt Updates von GitHub und lädt Daten neu
# Verwendung: .\deploy-updates.ps1 [--server-url http://localhost:3003]

param(
    [string]$ServerUrl = "http://localhost:3003"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment: Updates von GitHub laden" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Git Pull ausführen
Write-Host "[1/3] Hole Updates von GitHub..." -ForegroundColor Yellow
try {
    $gitOutput = git pull 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Git Pull erfolgreich" -ForegroundColor Green
        Write-Host $gitOutput -ForegroundColor Gray
    } else {
        Write-Host "⚠️ Git Pull mit Warnungen (Code: $LASTEXITCODE)" -ForegroundColor Yellow
        Write-Host $gitOutput -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Fehler beim Git Pull: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 2. Prüfe ob Server läuft
Write-Host "[2/3] Prüfe Server-Status..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$ServerUrl/api/debug/status" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✓ Server läuft auf $ServerUrl" -ForegroundColor Green
} catch {
    Write-Host "❌ Server nicht erreichbar auf $ServerUrl" -ForegroundColor Red
    Write-Host "   Bitte starte den Server zuerst mit: .\server-control.ps1 start" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# 3. Lade Lectures neu
Write-Host "[3/3] Lade Lectures-Daten neu..." -ForegroundColor Yellow
try {
    $reloadResponse = Invoke-RestMethod -Uri "$ServerUrl/api/reload-lectures" -Method POST -ContentType "application/json"
    if ($reloadResponse.success) {
        Write-Host "✓ Lectures erfolgreich neu geladen: $($reloadResponse.lecturesLoaded) Vorträge" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Reload mit Warnungen" -ForegroundColor Yellow
        Write-Host ($reloadResponse | ConvertTo-Json) -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Fehler beim Neuladen der Lectures: $_" -ForegroundColor Red
    Write-Host "   Response: $($_.Exception.Response)" -ForegroundColor Gray
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ Deployment abgeschlossen!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

