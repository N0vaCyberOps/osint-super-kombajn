FROM python:3.10-slim

# Ustaw zmienne środowiskowe
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Katalog roboczy
WORKDIR /app

# Instalacja zależności systemowych
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    exiftool \
    python3-dev \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Kopiuj pliki projektu
COPY . /app/

# Instaluj zależności Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Pobierz narzędzia OSINT
RUN mkdir -p /app/osint_tools/sherlock && \
    git clone https://github.com/sherlock-project/sherlock.git /app/osint_tools/sherlock && \
    cd /app/osint_tools/sherlock && \
    pip install -r requirements.txt

RUN mkdir -p /app/osint_tools/maigret && \
    git clone https://github.com/soxoj/maigret.git /app/osint_tools/maigret && \
    cd /app/osint_tools/maigret && \
    pip install -e .

RUN mkdir -p /app/osint_tools/holehe && \
    git clone https://github.com/megadose/holehe.git /app/osint_tools/holehe && \
    cd /app/osint_tools/holehe && \
    pip install -e .

# Utwórz katalogi dla danych
RUN mkdir -p /app/osint_tools/logs /app/osint_tools/results

# Entrypoint
ENTRYPOINT ["python", "main.py"]