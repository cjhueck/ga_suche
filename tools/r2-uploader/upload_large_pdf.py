import sys
import os
import time
import requests

WORKER_URL = "https://r2-uploader.ga-steiner.workers.dev"
AUTH_TOKEN = "steiner-upload-2026"
CHUNK_SIZE = 90 * 1024 * 1024  # 90 MB per part

def upload_large_file(local_path, r2_key):
    file_size = os.path.getsize(local_path)
    print(f"Datei: {local_path}")
    print(f"Groesse: {file_size / 1024 / 1024:.1f} MB")
    print(f"R2-Key: {r2_key}")
    print(f"Chunk-Groesse: {CHUNK_SIZE / 1024 / 1024:.0f} MB")
    num_parts = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE
    print(f"Teile: {num_parts}")
    print()

    headers = {"X-Auth-Token": AUTH_TOKEN}

    print("[1/3] Erstelle Multipart-Upload...")
    resp = requests.post(f"{WORKER_URL}/create?key={r2_key}", headers=headers)
    resp.raise_for_status()
    upload_id = resp.json()["uploadId"]
    print(f"  Upload-ID: {upload_id}")

    print(f"\n[2/3] Lade {num_parts} Teile hoch...")
    parts = []
    with open(local_path, "rb") as f:
        for part_num in range(1, num_parts + 1):
            chunk = f.read(CHUNK_SIZE)
            chunk_mb = len(chunk) / 1024 / 1024
            print(f"  Teil {part_num}/{num_parts} ({chunk_mb:.1f} MB)...", end=" ", flush=True)
            t0 = time.time()
            try:
                resp = requests.put(
                    f"{WORKER_URL}/upload-part?key={r2_key}&uploadId={upload_id}&partNumber={part_num}",
                    headers={**headers, "Content-Type": "application/octet-stream"},
                    data=chunk,
                    timeout=600,
                )
                resp.raise_for_status()
                part_result = resp.json()
                parts.append({
                    "partNumber": part_result["partNumber"],
                    "etag": part_result["etag"],
                })
                elapsed = time.time() - t0
                speed = chunk_mb / elapsed if elapsed > 0 else 0
                print(f"OK ({elapsed:.1f}s, {speed:.1f} MB/s)")
            except Exception as e:
                print(f"FEHLER: {e}")
                print(f"\nAbort Upload-ID: {upload_id}")
                try:
                    requests.delete(
                        f"{WORKER_URL}/abort?key={r2_key}&uploadId={upload_id}",
                        headers=headers,
                    )
                except:
                    pass
                sys.exit(1)

    print(f"\n[3/3] Finalisiere Upload...")
    resp = requests.post(
        f"{WORKER_URL}/complete?key={r2_key}&uploadId={upload_id}",
        headers={**headers, "Content-Type": "application/json"},
        json={"parts": parts},
    )
    resp.raise_for_status()
    print(f"  Ergebnis: {resp.json()}")
    print(f"\nFertig! {r2_key} auf R2 hochgeladen.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: python {sys.argv[0]} <local_path> <r2_key>")
        sys.exit(1)
    upload_large_file(sys.argv[1], sys.argv[2])
