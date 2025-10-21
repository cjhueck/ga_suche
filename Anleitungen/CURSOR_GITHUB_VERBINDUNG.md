# Cursor mit GitHub Account verbinden

## Übersicht
Diese Anleitung zeigt dir, wie du deinen Desktop Cursor Editor mit deinem GitHub Account verbindest.

## Methoden zur Verbindung

### Methode 1: GitHub CLI (gh) - Bereits konfiguriert ✓

Dein System ist bereits über die GitHub CLI authentifiziert. Du kannst dies überprüfen mit:

```bash
gh auth status
```

Status: **Bereits verbunden** mit github.com

### Methode 2: Git-Konfiguration mit Personal Access Token

Deine Git-Konfiguration ist bereits mit einem GitHub Access Token eingerichtet:

```bash
git config --global user.name "Dein Name"
git config --global user.email "deine@email.com"
```

Der Token ist bereits in der Git-Konfiguration hinterlegt und ermöglicht:
- Push und Pull von/zu GitHub Repositories
- Authentifizierung für Git-Operationen
- Zugriff auf private Repositories

### Methode 3: Cursor IDE Einstellungen

Um Cursor direkt mit deinem GitHub Account zu verbinden:

1. **Öffne Cursor Einstellungen**
   - Windows/Linux: `Ctrl + ,` oder Datei → Einstellungen
   - Mac: `Cmd + ,` oder Cursor → Einstellungen

2. **Navigiere zu "Accounts"** oder suche nach "GitHub"

3. **Wähle "Sign in with GitHub"**
   - Ein Browser-Fenster öffnet sich
   - Melde dich bei GitHub an
   - Autorisiere Cursor den Zugriff

4. **Bestätige die Verbindung**
   - Nach erfolgreicher Authentifizierung erscheint dein GitHub-Benutzername in Cursor

## Funktionen nach der Verbindung

Nach erfolgreicher Verbindung kannst du:

- ✓ GitHub Repositories direkt in Cursor klonen
- ✓ Pull Requests erstellen und verwalten
- ✓ Issues bearbeiten
- ✓ Commits pushen und pullen
- ✓ GitHub Copilot nutzen (falls Abonnement vorhanden)
- ✓ Gists erstellen und teilen

## Aktuelle Konfiguration

**Git User:**
```
Name: Cursor Agent
Email: cursoragent@cursor.com
```

**Repository:**
```
https://github.com/cjhueck/ga_suche
```

**Status:** Authentifizierung ist aktiv und funktioniert

## Problembehebung

### Token abgelaufen?

Wenn dein Access Token abläuft, musst du:

1. Neuen Personal Access Token auf GitHub erstellen:
   - Gehe zu GitHub.com → Settings → Developer settings → Personal access tokens
   - Wähle "Generate new token (classic)"
   - Setze erforderliche Scopes (repo, workflow, etc.)
   - Kopiere den Token

2. Token in Git-Konfiguration aktualisieren:
   ```bash
   gh auth login
   ```

### Verbindung testen

```bash
# Test GitHub CLI
gh auth status

# Test Git-Verbindung
git ls-remote https://github.com/cjhueck/ga_suche

# Test mit einem Push (auf aktuellem Branch)
git push origin HEAD
```

## Weitere Ressourcen

- [GitHub CLI Dokumentation](https://cli.github.com/manual/)
- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [Cursor Dokumentation](https://docs.cursor.com)

---

**Erstellt:** 2025-10-21  
**Version:** 1.0
