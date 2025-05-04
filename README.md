# OSINT Super Kombajn

OSINT Super Kombajn to kompleksowe narzędzie do zbierania i analizy informacji z otwartych źródeł (OSINT - Open Source Intelligence). Aplikacja integruje popularne narzędzia OSINT w jednym interfejsie, umożliwiając efektywne wyszukiwanie informacji o użytkownikach, numerach telefonów, adresach e-mail i plikach.

## Funkcje

- **Wyszukiwanie profili użytkowników** - znajdowanie profili na różnych platformach społecznościowych (Maigret, Sherlock)
- **Analiza numerów telefonów** - zbieranie informacji o numerach telefonów (PhoneInfoga)
- **Weryfikacja adresów e-mail** - sprawdzanie, na jakich serwisach zarejestrowany jest adres e-mail (Holehe)
- **Analiza metadanych plików** - ekstrakcja metadanych z plików (ExifTool)
- **Generowanie raportów** - tworzenie raportów w formatach HTML, JSON, TXT i PDF
- **Analiza AI** - opcjonalna analiza zebranych danych przy użyciu modeli AI

## Wymagania

- Python 3.8+
- Zainstalowane narzędzia zewnętrzne:
  - Python (dla Maigret, Sherlock, Holehe)
  - Docker (dla PhoneInfoga)
  - ExifTool

## Instalacja

1. Sklonuj repozytorium:
   ```bash
   git clone https://github.com/twoje-konto/OSINT-Super-Kombajn.git
   cd OSINT-Super-Kombajn
   ```

2. Zainstaluj zależności:
   ```bash
   pip install -r requirements.txt
   ```

3. Skonfiguruj narzędzia zewnętrzne:
   - Maigret: `git clone https://github.com/soxoj/maigret.git osint_tools/tools/maigret`
   - Sherlock: `git clone https://github.com/sherlock-project/sherlock.git osint_tools/tools/sherlock`
   - Holehe: `git clone https://github.com/megadose/holehe.git osint_tools/tools/holehe`
   - ExifTool: Zainstaluj zgodnie z instrukcjami dla Twojego systemu operacyjnego
   - PhoneInfoga: Upewnij się, że Docker jest zainstalowany i działa

## Użycie

### Linia poleceń

```bash
# Wyszukiwanie profili użytkownika
python -m osint_tools.main --username jankowalski

# Analiza numeru telefonu
python -m osint_tools.main --phone "+48123456789"

# Weryfikacja adresu e-mail
python -m osint_tools.main --email jan.kowalski@example.com

# Analiza metadanych pliku
python -m osint_tools.main --file /path/to/image.jpg

# Generowanie raportu
python -m osint_tools.main --username jankowalski --report --report-format html

# Analiza AI (jeśli włączona)
python -m osint_tools.main --username jankowalski --analyze
```

### Opcje

- `--username` - nazwa użytkownika do wyszukania
- `--phone` - numer telefonu do analizy
- `--email` - adres e-mail do weryfikacji
- `--file` - ścieżka do pliku do analizy metadanych
- `--all` - wykonaj wszystkie możliwe analizy
- `--analyze` - uruchom analizę AI wyników
- `--report` - generuj raport z wyników
- `--report-format` - format raportu (html, json, txt, pdf)
- `--config` - ścieżka do pliku konfiguracyjnego
- `--output-dir` - katalog dla plików wyjściowych
- `--verbose` - tryb szczegółowego logowania

## Konfiguracja

Konfiguracja jest przechowywana w pliku `osint_tools/configs/settings.yaml`. Możesz dostosować następujące ustawienia:

- Limity czasu i liczby ponownych prób dla narzędzi
- Ustawienia logowania
- Konfiguracja API AI
- Ustawienia wydajności i bezpieczeństwa
- Opcje raportowania

Przykład:

```yaml
# Konfiguracja OSINT Super Kombajn
version: "0.2.0"

# Ustawienia logowania
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "json"  # json lub text
  max_files: 10
  max_size_mb: 10

# Konfiguracja narzędzi
tools:
  sherlock:
    timeout: 300
    max_retries: 3
  
  phoneinfoga:
    timeout: 300
    max_retries: 3
  
  # ... inne narzędzia ...

# Konfiguracja API
api:
  ai:
    enabled: false
    provider: "openrouter"
    model: "anthropic/claude-3-opus-20240229"
    rate_limit: 5
    retry_attempts: 3

# ... inne ustawienia ...
```

## Struktura projektu

```
osint_tools/
├── configs/           # Pliki konfiguracyjne
├── core/              # Główne komponenty
│   ├── base_adapter.py # Bazowa klasa adaptera
│   ├── command.py     # Implementacja wzorca Command
│   ├── worker.py      # Pula asynchronicznych pracowników
│   ├── metrics.py     # Zbieranie metryk
│   ├── report.py      # Generowanie raportów
│   └── analyzers.py   # Analizatory AI
├── logs/              # Logi aplikacji
├── results/           # Wyniki analiz
├── templates/         # Szablony raportów
├── tools/             # Adaptery narzędzi
│   ├── exiftool/      # Adapter ExifTool
│   ├── holehe/        # Adapter Holehe
│   ├── maigret/       # Adapter Maigret
│   ├── phoneinfoga/   # Adapter PhoneInfoga
│   └── sherlock/      # Adapter Sherlock
├── utils/             # Narzędzia pomocnicze
│   ├── config.py      # Zarządzanie konfiguracją
│   ├── logger.py      # Logowanie
│   └── validators.py  # Walidacja danych wejściowych
└── main.py            # Punkt wejścia aplikacji
```

## Testowanie

Uruchom testy za pomocą pytest:

```bash
pytest
```

Uruchom tylko testy jednostkowe:

```bash
pytest -m unit
```

## Licencja

Ten projekt jest udostępniany na licencji MIT. Zobacz plik LICENSE, aby uzyskać więcej informacji.

## Autorzy

- Twoje Imię i Nazwisko - [twój-email@example.com](mailto:twój-email@example.com)

## Podziękowania

- [Maigret](https://github.com/soxoj/maigret)
- [Sherlock](https://github.com/sherlock-project/sherlock)
- [PhoneInfoga](https://github.com/sundowndev/phoneinfoga)
- [Holehe](https://github.com/megadose/holehe)
- [ExifTool](https://exiftool.org/)
