# Server Control Script für backend.js
param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("start", "stop", "restart", "status")]
    [string]$Action = "status"
)

# Aktualisiere PATH mit System- und User-Umgebungsvariablen
$env:PATH = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $scriptPath "backend.js"
$port = 3003

function Stop-Server {
    Write-Host "Stoppe Server auf Port $port..." -ForegroundColor Yellow
    
    # Suche nach Prozessen, die Port 3003 verwenden
    $netstat = netstat -ano | Select-String ":$port.*LISTENING"
    if ($netstat) {
        $pids = $netstat | ForEach-Object {
            ($_ -split '\s+')[-1]
        } | Select-Object -Unique
        
        foreach ($pid in $pids) {
            Write-Host "Beende Prozess $pid (verwendet Port $port)..." -ForegroundColor Yellow
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        }
        Write-Host "Server gestoppt." -ForegroundColor Green
    } else {
        Write-Host "Kein Server auf Port $port gefunden." -ForegroundColor Gray
    }
}

function Start-Server {
    Write-Host "Starte Server..." -ForegroundColor Cyan
    
    # Prüfe ob Server bereits läuft
    $netstat = netstat -ano | Select-String ":$port.*LISTENING"
    if ($netstat) {
        Write-Host "Server läuft bereits auf Port $port!" -ForegroundColor Yellow
        return
    }
    
    Set-Location $scriptPath
    
    # Starte Server im Hintergrund
    Start-Process -FilePath "node" -ArgumentList $backendPath -WorkingDirectory $scriptPath -WindowStyle Hidden
    
    Start-Sleep -Seconds 2
    
    # Prüfe ob Server gestartet wurde
    $netstat = netstat -ano | Select-String ":$port.*LISTENING"
    if ($netstat) {
        Write-Host "Server erfolgreich gestartet auf http://localhost:$port" -ForegroundColor Green
    } else {
        Write-Host "Server konnte nicht gestartet werden." -ForegroundColor Red
    }
}

function Get-ServerStatus {
    $netstat = netstat -ano | Select-String ":$port.*LISTENING"
    if ($netstat) {
        Write-Host "Server läuft auf Port $port" -ForegroundColor Green
        Write-Host "URL: http://localhost:$port" -ForegroundColor Cyan
    } else {
        Write-Host "Server läuft nicht." -ForegroundColor Gray
    }
}

# Führe Aktion aus
switch ($Action) {
    "start" {
        Start-Server
    }
    "stop" {
        Stop-Server
    }
    "restart" {
        Stop-Server
        Start-Sleep -Seconds 1
        Start-Server
    }
    "status" {
        Get-ServerStatus
    }
}

