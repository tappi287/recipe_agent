#!/bin/bash
set -e

REPO_URL="https://github.com/tappi287/recipe_agent.git"
REPO_DIR="/app/repo"

echo "Prüfe Repository-Status..."

# Wenn das Repository bereits geklont wurde
if [ -d "$REPO_DIR/.git" ]; then
    echo "Repository bereits vorhanden, aktualisiere..."
    cd $REPO_DIR
    git fetch
    git reset --hard origin/main
else
    echo "Klone Repository..."
    # Entferne den Verzeichnisinhalt, falls er existiert
    rm -rf $REPO_DIR
    # Klone das Repository
    git clone $REPO_URL $REPO_DIR
    cd $REPO_DIR
fi

echo "Repository aktualisiert!"

# Installiere die Abhängigkeiten mit uv sync
echo "Synchronisiere Abhängigkeiten mit uv sync..."
cd $REPO_DIR
uv sync --frozen

# Führe die Anwendung aus
echo "Starte Anwendung..."
exec uv run bot
