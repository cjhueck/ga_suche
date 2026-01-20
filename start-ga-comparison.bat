@echo off
echo Starting GA Text Comparison...
echo.

:: Start Node.js server (nb) in background on port 3003
start "GA Node Server" /min cmd /c "nb"

:: Start Python API server in background on port 3004
start "GA API Server" /min python ga_comparison_server.py

:: Wait for servers to start
echo Warte auf Server-Start...
timeout /t 3 /nobreak >nul

:: Open browser
start http://localhost:3003/ga-text-comparison.html

echo.
echo Node Server (nb) laeuft auf Port 3003
echo API Server laeuft auf Port 3004
echo Browser oeffnet http://localhost:3003/ga-text-comparison.html
echo.
echo Druecken Sie eine Taste zum Beenden beider Server...
pause >nul

:: Kill both servers when done
taskkill /FI "WINDOWTITLE eq GA Node Server*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq GA API Server*" /F >nul 2>&1
echo Server beendet.
