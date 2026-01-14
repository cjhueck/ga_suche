# -*- coding: utf-8 -*-
"""
Skript zum Zusammenführen aller Analytics-Backups und Wiederherstellung kumulativer Daten

Dieses Skript:
1. Lädt alle Backup-Dateien aus backups/analytics/
2. Führt tägliche Statistiken zusammen (verwendet neueste Werte bei Duplikaten)
3. Führt topSearches und topLectures zusammen (summiert Werte)
4. Berechnet kumulative Werte neu
5. Speichert die wiederhergestellte analytics-data.json
"""

import json
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Pfade
BACKUP_DIR = Path('backups/analytics')
OUTPUT_FILE = Path('analytics-data.json')
PRE_RESTORE_BACKUP = Path('analytics-data.pre-restore.json')

def load_backup_files():
    """Lädt alle Backup-Dateien und sortiert sie nach Datum"""
    backups = []
    
    if not BACKUP_DIR.exists():
        print(f"[FEHLER] Backup-Verzeichnis nicht gefunden: {BACKUP_DIR}")
        return []
    
    for file in BACKUP_DIR.glob('analytics-data-*.json'):
        try:
            # Extrahiere Datum aus Dateinamen
            date_match = file.stem.replace('analytics-data-', '')
            date_obj = datetime.strptime(date_match, '%Y-%m-%d')
            
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            backups.append({
                'file': file,
                'date': date_obj,
                'data': data
            })
            print(f"[OK] Backup geladen: {file.name} ({date_obj.strftime('%Y-%m-%d')})")
        except Exception as e:
            print(f"[WARN] Fehler beim Laden von {file.name}: {e}")
    
    # Sortiere nach Datum (älteste zuerst)
    backups.sort(key=lambda x: x['date'])
    return backups

def merge_daily_stats(backups):
    """Führt tägliche Statistiken zusammen - verwendet neueste Werte bei Duplikaten"""
    merged_daily_stats = {}
    
    for backup in backups:
        daily_stats = backup['data'].get('dailyStats', {})
        backup_date = backup['date'].strftime('%Y-%m-%d')
        
        for date_key, day_data in daily_stats.items():
            # Wenn dieser Tag bereits existiert, verwende die neuesten Werte
            # (spätere Backups haben Vorrang)
            if date_key not in merged_daily_stats:
                merged_daily_stats[date_key] = {
                    'views': day_data.get('views', 0),
                    'searches': day_data.get('searches', 0),
                    'lectures': day_data.get('lectures', 0)
                }
            else:
                # Verwende Maximum der Werte (falls unterschiedlich)
                # Oder einfach die neuesten Werte
                merged_daily_stats[date_key] = {
                    'views': max(merged_daily_stats[date_key]['views'], day_data.get('views', 0)),
                    'searches': max(merged_daily_stats[date_key]['searches'], day_data.get('searches', 0)),
                    'lectures': max(merged_daily_stats[date_key]['lectures'], day_data.get('lectures', 0))
                }
    
    return merged_daily_stats

def merge_top_searches(backups):
    """Führt Top-Searches zusammen - summiert Werte"""
    merged_searches = defaultdict(int)
    
    for backup in backups:
        top_searches = backup['data'].get('topSearches', {})
        for term, count in top_searches.items():
            merged_searches[term] += count
    
    return dict(merged_searches)

def merge_top_lectures(backups):
    """Führt Top-Lectures zusammen - summiert Werte"""
    merged_lectures = defaultdict(int)
    
    for backup in backups:
        top_lectures = backup['data'].get('topLectures', {})
        for lecture_id, count in top_lectures.items():
            merged_lectures[lecture_id] += count
    
    return dict(merged_lectures)

def calculate_cumulative_values(daily_stats):
    """Berechnet kumulative Werte aus täglichen Statistiken"""
    total_views = 0
    total_searches = 0
    total_lectures = 0
    
    for date_key, day_data in daily_stats.items():
        total_views += day_data.get('views', 0)
        total_searches += day_data.get('searches', 0)
        total_lectures += day_data.get('lectures', 0)
    
    return total_views, total_searches, total_lectures

def main():
    print("=" * 70)
    print("Analytics-Backup Wiederherstellung")
    print("=" * 70)
    print()
    
    # Lade alle Backups
    backups = load_backup_files()
    
    if not backups:
        print("[FEHLER] Keine Backup-Dateien gefunden!")
        return
    
    print(f"\n[INFO] {len(backups)} Backup-Dateien gefunden")
    print()
    
    # Erstelle Backup der aktuellen Datei (falls vorhanden)
    if OUTPUT_FILE.exists():
        print(f"[INFO] Erstelle Backup der aktuellen Datei...")
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
            with open(PRE_RESTORE_BACKUP, 'w', encoding='utf-8') as f:
                json.dump(current_data, f, indent=2, ensure_ascii=False)
            print(f"[OK] Aktuelle Datei gesichert als: {PRE_RESTORE_BACKUP}")
        except Exception as e:
            print(f"[WARN] Fehler beim Erstellen des Backups: {e}")
    
    print()
    
    # Führe Daten zusammen
    print("[INFO] Fuehre Daten zusammen...")
    merged_daily_stats = merge_daily_stats(backups)
    merged_top_searches = merge_top_searches(backups)
    merged_top_lectures = merge_top_lectures(backups)
    
    # Berechne kumulative Werte
    total_views, total_searches, total_lectures = calculate_cumulative_values(merged_daily_stats)
    
    # Erstelle wiederhergestellte Datenstruktur
    restored_data = {
        'dailyStats': merged_daily_stats,
        'topSearches': merged_top_searches,
        'topLectures': merged_top_lectures,
        'totalViews': total_views,
        'totalSearches': total_searches,
        'totalLectureViews': total_lectures
    }
    
    # Speichere wiederhergestellte Datei
    print(f"\n[INFO] Speichere wiederhergestellte Daten...")
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(restored_data, f, indent=2, ensure_ascii=False)
        print(f"[OK] Daten gespeichert in: {OUTPUT_FILE}")
    except Exception as e:
        print(f"[FEHLER] Fehler beim Speichern: {e}")
        return
    
    # Zeige Zusammenfassung
    print()
    print("=" * 70)
    print("Zusammenfassung")
    print("=" * 70)
    print(f"Tage mit Daten: {len(merged_daily_stats)}")
    print(f"Eindeutige Suchbegriffe: {len(merged_top_searches)}")
    print(f"Eindeutige Vortraege: {len(merged_top_lectures)}")
    print()
    print("Kumulative Werte:")
    print(f"  Gesamt Views: {total_views}")
    print(f"  Gesamt Suchen: {total_searches}")
    print(f"  Gesamt Vortraege: {total_lectures}")
    print()
    
    # Zeige Datumsbereich
    if merged_daily_stats:
        dates = sorted(merged_daily_stats.keys())
        print(f"Datumsbereich: {dates[0]} bis {dates[-1]}")
        print()
    
    # Zeige Top 5 Suchen und Vorträge
    if merged_top_searches:
        top_5_searches = sorted(merged_top_searches.items(), key=lambda x: x[1], reverse=True)[:5]
        print("Top 5 Suchbegriffe:")
        for term, count in top_5_searches:
            print(f"  - {term}: {count}")
        print()
    
    if merged_top_lectures:
        top_5_lectures = sorted(merged_top_lectures.items(), key=lambda x: x[1], reverse=True)[:5]
        print("Top 5 Vortraege:")
        for lecture_id, count in top_5_lectures:
            print(f"  - {lecture_id}: {count}")
        print()
    
    print("[OK] Wiederherstellung abgeschlossen!")
    print()
    print(f"[TIP] Die urspruengliche Datei wurde als {PRE_RESTORE_BACKUP} gesichert")
    print("      Falls etwas schiefgeht, koennen Sie diese wiederherstellen.")

if __name__ == '__main__':
    main()

