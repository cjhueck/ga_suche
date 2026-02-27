import subprocess, time, os, sys

# Alle node-Prozesse beenden
result = subprocess.run(['taskkill', '/F', '/IM', 'node.exe'], capture_output=True, text=True, timeout=10)
print('Kill:', result.stdout.strip() or result.stderr.strip())
time.sleep(2)

# Neuen Server starten
proc = subprocess.Popen(
    ['node', 'backend.js'],
    cwd=r'C:\Users\chuec\OneDrive\GitHub\ga_suche',
    creationflags=0x00000008,  # DETACHED_PROCESS
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
print(f'Server gestartet, PID: {proc.pid}')
time.sleep(3)

# Prüfen
import socket
s = socket.socket()
s.settimeout(3)
try:
    s.connect(('localhost', 3003))
    print('Port 3003: OK (erreichbar)')
except:
    print('Port 3003: noch nicht bereit (normal - gibt 5 Sek)')
finally:
    s.close()
