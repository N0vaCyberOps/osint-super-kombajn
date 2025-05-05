# 🕵️ OSINT Super Kombajn

**OSINT Super Kombajn** to profesjonalny, modularny system analizy OSINT oparty na Pythonie 3.10+, integrujący klasyczne narzędzia OSINT i sztuczną inteligencję (AI).

## 📋 Opis

OSINT Super Kombajn to kompleksowe narzędzie do zbierania i analizy informacji z otwartych źródeł (OSINT - Open Source Intelligence). System integruje popularne narzędzia OSINT, takie jak:

- **Sherlock** - wyszukiwanie kont użytkowników w mediach społecznościowych
- **PhoneInfoga** - analiza numerów telefonów
- **Maigret** - zaawansowane wyszukiwanie profili użytkowników
- **ExifTool** - analiza metadanych plików
- **Holehe** - sprawdzanie użycia adresów e-mail na różnych serwisach

Dodatkowo, system wykorzystuje sztuczną inteligencję do analizy zebranych danych, co pozwala na głębsze zrozumienie i interpretację wyników.

## 🚀 Funkcje

- Modułowa architektura pozwalająca na łatwe dodawanie nowych narzędzi
- Asynchroniczne przetwarzanie dla szybszego działania
- Integracja z narzędziami OSINT
- Analiza AI zebranych danych
- Generowanie raportów w różnych formatach
- Interfejs wiersza poleceń (CLI)

## 🔧 Instalacja

```bash
# Klonowanie repozytorium
git clone https://github.com/yourusername/OSINT-Super-Kombajn.git
cd OSINT-Super-Kombajn

# Instalacja zależności
pip install -e .

# Instalacja zależności deweloperskich (opcjonalnie)
pip install -e ".[dev]"
```

## 📊 Użycie

```bash
# Podstawowe użycie
osint-kombajn --username jankowalski

# Analiza numeru telefonu
osint-kombajn --phone "+48123456789"

# Analiza adresu e-mail
osint-kombajn --email jan.kowalski@example.com

# Analiza metadanych pliku
osint-kombajn --file zdjecie.jpg

# Uruchomienie wszystkich dostępnych analiz
osint-kombajn --all --username jankowalski --phone "+48123456789" --email jan.kowalski@example.com
```

## 🧩 Struktura projektu

```
OSINT-Super-Kombajn/
├── src/
│   └── osint_super_kombajn/
│       ├── __init__.py
│       ├── main.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── engine.py
│       │   └── event_bus.py
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── sherlock/
│       │   ├── phoneinfoga/
│       │   ├── maigret/
│       │   ├── exiftool/
│       │   └── holehe/
│       ├── ai_agents/
│       │   ├── __init__.py
│       │   └── analyzers.py
│       └── utils/
│           ├── __init__.py
│           ├── validators.py
│           └── logger.py
├── tests/
│   └── __init__.py
├── docs/
├── pyproject.toml
└── README.md
```

## 📝 Licencja

Ten projekt jest dostępny na licencji MIT. Zobacz plik `LICENSE` dla szczegółów.

## 🤝 Współpraca

Zachęcamy do współpracy przy rozwoju projektu. Jeśli chcesz dodać nowe funkcje, naprawić błędy lub ulepszyć dokumentację, prosimy o utworzenie pull requesta.

## 📞 Kontakt

- Autor: Autor OSINT Super Kombajn
- Email: kontakt@przyklad.com
