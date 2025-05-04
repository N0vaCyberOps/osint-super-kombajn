"""
Główny moduł OSINT Super Kombajn zawierający punkt wejścia do aplikacji.

Zarządza przetwarzaniem argumentów wiersza poleceń, inicjalizuje narzędzia OSINT
i generuje raporty na podstawie wyników analiz.
"""

import argparse
import asyncio
import sys
import os
from pathlib import Path
import traceback

from osint_tools.core.engine import OSINTEngine


async def run_app() -> int:
    """Główna funkcja uruchamiająca aplikację."""
    parser = argparse.ArgumentParser(description="OSINT Super Kombajn - zbiór narzędzi do badań OSINT")
    
    # Dane wejściowe
    input_group = parser.add_argument_group("Dane wejściowe")
    input_group.add_argument("--username", type=str, help="Nazwa użytkownika do analizy")
    input_group.add_argument("--phone", type=str, help="Numer telefonu do analizy")
    input_group.add_argument("--email", type=str, help="Adres e-mail do analizy")
    input_group.add_argument("--file", type=str, help="Ścieżka do pliku (analiza metadanych)")
    
    # Tryby działania
    mode_group = parser.add_argument_group("Tryby działania")
    mode_group.add_argument("--all", action="store_true", help="Wykonaj wszystkie możliwe analizy")
    
    # Raportowanie
    report_group = parser.add_argument_group("Raportowanie")
    report_group.add_argument("--html-report", action="store_true", help="Generuj raport HTML")
    report_group.add_argument("--output-dir", type=str, help="Katalog dla plików wyjściowych")
    
    # Konfiguracja
    config_group = parser.add_argument_group("Konfiguracja")
    config_group.add_argument("--config", type=str, help="Ścieżka do pliku konfiguracyjnego")
    config_group.add_argument("--verbose", "-v", action="store_true", help="Tryb szczegółowego logowania")
    
    args = parser.parse_args()
    
    try:
        engine = OSINTEngine(
            results_dir=Path(args.output_dir) if args.output_dir else None,
            verbose=args.verbose
        )
        
        if not any([args.username, args.email, args.phone, args.file]):
            print("Nie określono żadnych danych wejściowych (--username, --phone, --email, --file)")
            print("Podaj co najmniej jeden typ danych wejściowych do analizy.")
            return 1
            
        # Uruchom wszystkie narzędzia dla podanych danych wejściowych
        results = await engine.run_all(
            email=args.email,
            username=args.username,
            phone=args.phone,
            file_path=args.file
        )
        
        # Wyświetl podsumowanie
        engine.print_summary(results)
        
        # Generuj raport HTML jeśli potrzebny
        if args.html_report:
            report_path = engine.save_html_report(results)
            print(f"\nRaport HTML wygenerowany: {report_path}")
        
        success_count = sum(1 for r in results.values() if r.get("success", False))
        return 0 if success_count > 0 else 1
    
    except KeyboardInterrupt:
        print("\nOperacja przerwana przez użytkownika")
        return 130
    except Exception as e:
        print(f"Błąd inicjalizacji aplikacji: {e}")
        traceback.print_exc()
        return 1


def main() -> None:
    """Punkt wejścia dla aplikacji."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    exit_code = asyncio.run(run_app())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()