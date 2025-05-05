FROM python:3.11-slim@sha256:75a17dd6f00b277975715fc094c4a1570d512708de6bb4c5dc130814813ebfe4

WORKDIR /app

# Kopiowanie plików projektu
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Instalacja zależności
RUN pip install --no-cache-dir -e .

# Utworzenie katalogów na wyniki i logi
RUN mkdir -p results logs

# Ustawienie zmiennych środowiskowych
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Uruchomienie aplikacji
ENTRYPOINT ["python", "-m", "osint_super_kombajn.main"]
CMD ["--help"]
