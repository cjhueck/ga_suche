# Einfaches Startskript für backend.js
# Aktualisiere PATH mit System- und User-Umgebungsvariablen
$env:PATH = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host "Starte Backend-Server..." -ForegroundColor Cyan
node backend.js



