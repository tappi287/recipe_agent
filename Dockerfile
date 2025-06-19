FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Installiere Git und andere Abhängigkeiten
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Kopiere das Startup-Script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 8000

# Starte das Startup-Script, das das Repository klont und die Anwendung ausführt
CMD ["/app/start.sh"]