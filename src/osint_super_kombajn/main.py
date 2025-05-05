"""
Główny punkt wejścia OSINT Super Kombajn.
"""
import sys
import asyncio
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

from osint_super_kombajn.core.engine import OSINTEngine
from osint_super_kombajn.core.event_bus import event_bus
from osint_super_kombajn.utils.validators import validate_email
from osint_super_kombajn.config import config

def parse_arguments() -> argparse.Namespace:
    """
    Parsuje argumenty wiersza poleceń.
    
    Returns:
        Sparsowane argumenty
    """
    parser = argparse.ArgumentParser(
        description="OSINT Super Kombajn - zbiór narzędzi do badań OSINT"
    )
    parser.add_argument(
        "--username", 
        type=str, 
        help="Nazwa użytkownika do analizy"
    )
    parser.add_argument(
        "--phone", 
        type=str, 
        help="Numer telefonu do analizy"
    )
    parser.add_argument(
        "--email", 
        type=str, 
        help="Adres e-mail do analizy"
    )
    parser.add_argument(
        "--file", 
        type=str, 
        help="Ścieżka do pliku (analiza metadanych)"
    )
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="Wykonaj wszystkie możliwe analizy"
    )
    parser.add_argument(
        "--config", 
        type=str, 
        help="Ścieżka do pliku konfiguracyjnego"
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        help="Katalog dla plików wyjściowych"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Tryb szczegółowego logowania"
    )
    
    return parser.parse_args()

async def run_app() -> int:
    """
    Główna funkcja aplikacji.
    
    Returns:
        Kod wyjścia (0 dla sukcesu, wartość niezerowa dla błędów)
    """
    args = parse_arguments()
    
    # Inicjalizacja silnika OSINT
    engine = OSINTEngine()
    
    # Rejestracja zdarzeń
    await event_bus.publish("app_start", {"args": vars(args)})
    
    results = {}
    
    try:
        # Wykonaj analizy w zależności od podanych argumentów
        if args.username:
            print(f"Analizuję nazwę użytkownika: {args.username}")
            results["username"] = await engine.analyze_username(args.username)
            
        if args.phone:
            print(f"Analizuję numer telefonu: {args.phone}")
            results["phone"] = await engine.analyze_phone(args.phone)
            
        if args.email:
            if validate_email(args.email):
                print(f"Analizuję adres e-mail: {args.email}")
                results["email"] = await engine.analyze_email(args.email)
            else:
                print(f"Nieprawidłowy format adresu e-mail: {args.email}")
                
        if args.file:
            file_path = Path(args.file)
            if file_path.exists() and file_path.is_file():
                print(f"Analizuję plik: {args.file}")
                results["file"] = await engine.analyze_file(str(file_path))
            else:
                print(f"Plik nie istnieje lub nie jest plikiem: {args.file}")
        
        # Jeśli są jakieś wyniki, wykonaj analizę AI
        if results and config["ai"]["enabled"]:
            print("Wykonuję analizę AI zebranych danych...")
            ai_results = await engine.run_ai_analysis(results)
            results["ai_analysis"] = ai_results
            
        # Publikuj zdarzenie z wynikami
        await event_bus.publish("analysis_complete", {"results": results})
        
        # Wyświetl podsumowanie
        print("\nPodsumowanie analizy:")
        for key, value in results.items():
            if key != "ai_analysis":
                print(f"- {key}: Znaleziono dane")
        
        if "ai_analysis" in results:
            print("- Wykonano analizę AI")
            
        return 0
        
    except KeyboardInterrupt:
        print("\nOperacja przerwana przez użytkownika")
        await event_bus.publish("app_interrupted", {})
        return 130
        
    except Exception as e:
        print(f"Błąd: {e}")
        await event_bus.publish("app_error", {"error": str(e)})
        return 1
        
    finally:
        await event_bus.publish("app_shutdown", {})

def main() -> None:
    """
    Punkt wejścia dla aplikacji.
    """
    # Ustaw politykę pętli zdarzeń dla Windows, jeśli potrzeba
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Uruchom funkcję główną i zakończ z odpowiednim kodem
    exit_code = asyncio.run(run_app())
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
