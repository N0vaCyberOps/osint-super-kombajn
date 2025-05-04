<<<<<<< HEAD
# 🕵️ OSINT Super Kombajn

**OSINT Super Kombajn** to profesjonalny, modułowy system analizy OSINT oparty na Pythonie 3.10+, integrujący klasyczne narzędzia OSINT i sztuczną inteligencję (AI). Przeznaczony do szybkiego i efektywnego zbierania danych z wielu źródeł oraz generowania czytelnych raportów w formacie HTML, JSON i TXT.

---

## 🚀 Kluczowe funkcjonalności:
- 🔎 **Wielomodułowe rozpoznanie** dla:
  - Nazw użytkowników,
  - Numerów telefonów,
  - Adresów e-mail,
  - Domen/IP,
  - Analizy plików (metadane).
  
- 🤖 **Zaawansowana analiza AI**:
  - Wykorzystanie GPT-4, Claude 3, DeepSeek, Gemini, Mistral,
  - Automatyczne generowanie podsumowań i ocen ryzyka.

- 📈 **Automatyczne raportowanie**:
  - HTML, JSON, TXT,
  - Strukturalne logowanie (JSONL).

---

## 📂 Struktura Projektu:
```
osint_super_kombajn/
├── src/
│   └── osint_super_kombajn/
│       ├── __init__.py
│       ├── main.py
│       ├── config/
│       ├── core/
│       ├── tools/
│       │   ├── sherlock/
│       │   ├── phoneinfoga/
│       │   ├── recon-ng/
│       │   ├── maigret/
│       │   ├── holehe/
│       │   └── exiftool/
│       ├── ai_agents/
│       └── utils/
├── tests/
│   └── __init__.py
└── docs/
```

---

## 🛠 Instalacja i Konfiguracja:
```bash
git clone https://github.com/username/OSINT-Super-Kombajn.git
cd OSINT-Super-Kombajn
pip install -e .
```

### 🐳 Docker (zalecane):

```bash
docker build -t osint_kombajn .
docker run -it osint_kombajn bash
```

---

## 🚦 Użycie CLI:

```bash
# Podstawowe użycie
osint-kombajn --username użytkownik
osint-kombajn --phone +48123456789
osint-kombajn --email przykład@domena.pl
osint-kombajn --file ./zdjęcie.jpg

# Uruchomienie wszystkich modułów
osint-kombajn --all --username użytkownik --phone +48123456789 --email przykład@domena.pl
```

---

## 📄 Generowanie Raportów:

* Wyniki automatycznie zapisywane w katalogu `results/`.
* Raporty HTML dostępne w `reports/`.

---

## 🧠 AI Moduły (OpenRouter API):

* GPT-4 Turbo: analiza tekstu i podsumowania
* Claude 3 Opus: analiza behawioralna
* Gemini Pro: analiza dokumentów PDF
* Mistral AI: szybkie analizy i ocena reputacji

---

## 🧪 Testowanie:

```bash
pytest tests/
```

---

## 📌 Wymagania Systemowe:

* Python ≥ 3.10
* Docker (zalecane)

---

## 🔒 Bezpieczeństwo:

* Brak przechowywania danych osobowych.
* Dane wejściowe anonimowo analizowane przez AI.

---

## 📞 Wsparcie i Rozwój:

* GitHub Issues: [github.com/username/OSINT-Super-Kombajn/issues](https://github.com/username/OSINT-Super-Kombajn/issues)

---

© 2025 | Wszelkie prawa zastrzeżone.
=======
# osint-super-kombajn
Profesjonalny modułowy system analizy OSINT oparty na Pythonie 3.10+
>>>>>>> 33df76787b5b8d41a49da5be4d8f29af7ea37c68
