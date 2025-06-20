#!/bin/bash
set -e

REPO_URL="https://github.com/tappi287/recipe_agent.git"
REPO_DIR="/app/repo"

echo "Prüfe Repository-Status..."

# Wenn das Repository bereits geklont wurde
if [ -d "$REPO_DIR/.git" ]; then
    echo "Repository bereits vorhanden, aktualisiere..."
    cd "$REPO_DIR"
    git fetch
    git reset --hard origin/main
else
    echo "Klone Repository..."
    # Prüfe ob der Ordner existiert
    if [ -d "$REPO_DIR" ]; then
        echo "Verzeichnis existiert bereits, überspringe das Entfernen..."
        # Stelle sicher, dass das Verzeichnis leer ist (ohne .git zu löschen, falls es existiert)
        find "$REPO_DIR" -mindepth 1 -maxdepth 1 -not -name ".git" -exec rm -rf {} \; 2>/dev/null || true
    else
        # Erstelle das Verzeichnis, falls es nicht existiert
        mkdir -p "$REPO_DIR"
    fi

    # Klone das Repository
    git clone "$REPO_URL" "$REPO_DIR"
    cd "$REPO_DIR"
fi

echo "Repository aktualisiert!"

# Installiere/aktualisiere Python-Abhängigkeiten aus dem geklonten Repository
if [ -f "requirements.txt" ]; then
    echo "Installiere/aktualisiere Python-Abhängigkeiten aus requirements.txt..."
    pip install -r requirements.txt
else
    echo "Keine requirements.txt im Repository gefunden. Überspringe Python-Abhängigkeitsinstallation."
fi

echo "Stelle PYTHONPATH ein..."
# Wenn Ihr Python-Paket 'recipe_agent' unter einem 'src'-Verzeichnis im Repository liegt:
if [ -d "$REPO_DIR/src" ]; then
    export PYTHONPATH="$PYTHONPATH:$REPO_DIR/src"
else
    # Andernfalls, wenn das Paket direkt im Repo-Root liegt:
    export PYTHONPATH="$PYTHONPATH:$REPO_DIR"
fi


# Prüfe ob Playwright Browser vorhanden sind
# Dies sollte nur einmal beim ersten Start in das persistente Volume installieren
if [ ! -d "/root/.cache/ms-playwright/chromium" ]; then # Spezifischer prüfen auf einen installierten Browser
    echo "Playwright Browser nicht gefunden, installiere..."
    # 'playwright install' installiert die Browser-Binaries, nicht das Python-Paket
    playwright install chromium --with-deps
else
    echo "Playwright Browser Verzeichnis gefunden, überspringe Installation..."
fi

# Führe die Anwendung aus
echo "Starte Anwendung..."
# Der Einstiegspunkt ist recipe_agent.bot:main
exec python -m recipe_agent.bot