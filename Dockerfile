FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Installiere Git und andere Abhängigkeiten
RUN apt-get update && apt-get install -y \
    git \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    && rm -rf /var/lib/apt/lists/*

RUN playwright install --with-deps

WORKDIR /app

# Kopiere das Startup-Script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Setze Umgebungsvariablen für Playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright

# Starte das Startup-Script, das das Repository klont und die Anwendung ausführt
CMD ["/app/start.sh"]