"""
Główny moduł OSINT Super Kombajn zawierający punkt wejścia do aplikacji.

Zarządza przetwarzaniem argumentów wiersza poleceń, inicjalizuje narzędzia OSINT
i generuje raporty na podstawie wyników analiz.
"""

import argparse
import asyncio
import sys
import os
import functools
from pathlib import Path
from typing import Dict, Optional, Any, List, Tuple
from datetime import datetime
import traceback

from .utils.logger import OSINTLogger
from .utils.config import ConfigManager
from .utils.validators import validate_input
from .core.worker import AsyncWorkerPool
from .core.command import ToolRegistry, OSINTCommand
from .core.report import ReportGenerator
from .core.metrics import MetricsCollector
from .core.analyzers import TextAnalyzer, ProfileAnalyzer, analyze_results

# Importy adapterów narzędzi
from .tools.sherlock.adapter import SherlockAdapter
from .tools.phoneinfoga.adapter import PhoneInfogaAdapter
from .tools.maigret.adapter import MaigretAdapter
from .tools.exiftool.adapter import ExifToolAdapter
from .tools.holehe.adapter import HoleheAdapter


def handle_exception(func):
    """Dekorator dla jednolitej obsługi wyjątków."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except asyncio.CancelledError:
            # Nie przechwytuj anulowania
            raise
        except Exception as e:
            # Pobierz logger z pierwszego argumentu (self) jeśli istnieje
            logger = getattr(args[0], "logger", None) if args else None
            if logger:
                logger.error(f"Wyjątek w {func.__name__}: {e}", exc_info=True)
                
            tb = traceback.format_exc()
            return {
                "success": False,
                "error": str(e),
                "exception_type": type(e).__name__,
                "traceback": tb
            }
    return wrapper


class OSINTSuite:
    """Główna klasa zarządzająca przepływem pracy OSINT Super Kombajn."""
    
    def __init__(
        self,
        base_dir: Optional[Path] = None,
        log_dir: Optional[Path] = None,
        results_dir: Optional[Path] = None,
        config_file: Optional[Path] = None,
        verbose: bool = False
    ) -> None:
        """
        Inicjalizuje instancję OSINTSuite.

        Args:
            base_dir: Katalog bazowy dla narzędzi OSINT.
            log_dir: Katalog do przechowywania logów.
            results_dir: Katalog wyjściowy dla wyników.
            config_file: Ścieżka do pliku konfiguracyjnego.
            verbose: Tryb szczegółowego logowania.
        """
        # Inicjalizacja ścieżek
        self.base_dir = base_dir or Path.cwd() / "osint_tools"
        self.log_dir = log_dir or self.base_dir / "logs"
        self.results_dir = results_dir or self.base_dir / "results" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.config_file = config_file or self.base_dir / "configs" / "settings.yaml"
        self.verbose = verbose

        # Tworzenie katalogów
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Inicjalizacja menadżera konfiguracji
        self.config_manager = ConfigManager(config_file=self.config_file)
        
        # Ładowanie konfiguracji
        self.config = self.config_manager.load()

        # Inicjalizacja loggera
        log_level = "DEBUG" if verbose else "INFO"
        self.logger = OSINTLogger(
            log_dir=self.log_dir, 
            level=log_level,
            app_name="osint_super_kombajn",
            log_format=self.config.get("logging", {}).get("format", "json")
        )
        self.logger.info("Inicjalizacja OSINT Super Kombajn", base_dir=str(self.base_dir))
        
        # Inicjalizacja metryki
        self.metrics = MetricsCollector(log_dir=self.log_dir)
        
        # Inicjalizacja puli asynchronicznych pracowników
        max_workers = self.config.get("performance", {}).get("max_workers", 5)
        self.worker_pool = AsyncWorkerPool(max_workers=max_workers)
        
        # Inicjalizacja rejestru narzędzi
        self.tool_registry = ToolRegistry()
        self._register_tools()
        
        # Inicjalizacja generatora raportów
        self.report_generator = ReportGenerator(templates_dir=self.base_dir / "templates")
        
    def _register_tools(self) -> None:
        """Rejestruje dostępne narzędzia OSINT."""
        # Sherlock
        sherlock_path = self.base_dir / "sherlock"
        sherlock_config = self.config.get("tools", {}).get("sherlock", {})
        sherlock_adapter = SherlockAdapter(
            sherlock_path=sherlock_path,
            timeout=sherlock_config.get("timeout", 300),
            max_retries=sherlock_config.get("max_retries", 3)
        )
        self.tool_registry.register("sherlock", sherlock_adapter)
        
        # PhoneInfoga
        phoneinfoga_config = self.config.get("tools", {}).get("phoneinfoga", {})
        phoneinfoga_adapter = PhoneInfogaAdapter(
            timeout=phoneinfoga_config.get("timeout", 300)
        )
        self.tool_registry.register("phoneinfoga", phoneinfoga_adapter)
        
        # Maigret
        maigret_path = self.base_dir / "maigret"
        maigret_config = self.config.get("tools", {}).get("maigret", {})
        maigret_adapter = MaigretAdapter(
            maigret_path=maigret_path,
            timeout=maigret_config.get("timeout", 300)
        )
        self.tool_registry.register("maigret", maigret_adapter)
        
        # ExifTool
        exiftool_config = self.config.get("tools", {}).get("exiftool", {})
        exiftool_adapter = ExifToolAdapter(
            timeout=exiftool_config.get("timeout", 300)
        )
        self.tool_registry.register("exiftool", exiftool_adapter)
        
        # Holehe
        holehe_path = self.base_dir / "holehe"
        holehe_config = self.config.get("tools", {}).get("holehe", {})
        holehe_adapter = HoleheAdapter(
            holehe_path=holehe_path,
            timeout=holehe_config.get("timeout", 300)
        )
        self.tool_registry.register("holehe", holehe_adapter)
        
    @handle_exception
    async def run_tool(self, tool_name: str, input_value: str, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Uruchamia pojedyncze narzędzie OSINT.
        
        Args:
            tool_name: Nazwa narzędzia do uruchomienia.
            input_value: Wartość wejściowa dla narzędzia.
            output_path: Ścieżka do zapisania wyników.
            
        Returns:
            Słownik zawierający wyniki wykonania narzędzia.
        """
        start_time = datetime.now()
        self.logger.info(f"Uruchamianie narzędzia {tool_name}", input=input_value, output_path=str(output_path) if output_path else None)
        
        # Pobierz adapter narzędzia z rejestru
        adapter = self.tool_registry.get(tool_name)
        if not adapter:
            self.logger.error(f"Nieznane narzędzie: {tool_name}")
            self.metrics.record_tool_execution(tool_name, False, start_time.timestamp(), "unknown_tool")
            return {"success": False, "error": f"Nieznane narzędzie: {tool_name}"}
        
        # Określ typ walidacji na podstawie narzędzia
        validation_type = {
            "sherlock": "username",
            "maigret": "username",
            "phoneinfoga": "phone",
            "holehe": "email",
            "exiftool": "file"
        }.get(tool_name, "none")
        
        # Walidacja danych wejściowych
        validation_result = validate_input(validation_type, input_value)
        if validation_result is not True:
            self.logger.error(f"Nieprawidłowe dane wejściowe dla {tool_name}: {validation_result}")
            self.metrics.record_tool_execution(tool_name, False, start_time.timestamp(), "validation_error")
            return {"success": False, "error": validation_result, "tool": tool_name}
        
        # Przygotuj ścieżkę wyjściową
        if output_path is None:
            if tool_name == "exiftool":
                file_name = Path(input_value).name
                output_path = self.results_dir / f"{tool_name}_{file_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            else:
                sanitized_input = input_value.replace('@', '_').replace('+', '')
                output_path = self.results_dir / f"{tool_name}_{sanitized_input}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
        # Uruchom narzędzie
        try:
            result = await adapter.execute(input_value, output_path)
            
            # Zapisz metrykę
            success = result.get("success", False)
            error_type = type(result.get("error", "")).__name__ if not success else None
            self.metrics.record_tool_execution(tool_name, success, start_time.timestamp(), error_type)
            
            # Dodaj metadane
            result["tool"] = tool_name
            result["execution_time_ms"] = (datetime.now() - start_time).total_seconds() * 1000
            
            # Logowanie wyniku
            if success:
                self.logger.info(f"Narzędzie {tool_name} zakończyło wykonanie pomyślnie", execution_time_ms=result["execution_time_ms"])
            else:
                self.logger.error(f"Narzędzie {tool_name} zwróciło błąd: {result.get('error')}", execution_time_ms=result["execution_time_ms"])
                
            return result
        except Exception as e:
            self.logger.error(f"Nieoczekiwany błąd podczas wykonywania {tool_name}: {e}", exc_info=True)
            self.metrics.record_tool_execution(tool_name, False, start_time.timestamp(), type(e).__name__)
            return {"success": False, "error": str(e), "tool": tool_name}
            
    @handle_exception
    async def run_batch(self, batch: Dict[str, Tuple[str, str, Optional[Path]]]) -> List[Dict[str, Any]]:
        """
        Uruchamia pakiet narzędzi równolegle.
        
        Args:
            batch: Słownik zadań w formacie {task_id: (tool_name, input_value, output_path)}
            
        Returns:
            Lista wyników wykonania narzędzi.
        """
        async def _run_task(task_id, tool_name, input_value, output_path):
            result = await self.run_tool(tool_name, input_value, output_path)
            result["task_id"] = task_id
            return result
            
        tasks = {}
        for task_id, (tool_name, input_value, output_path) in batch.items():
            tasks[task_id] = functools.partial(_run_task, task_id, tool_name, input_value, output_path)
            
        results = await self.worker_pool.execute_batch(tasks)
        return list(results.values())

    @handle_exception
    async def main(self, args: argparse.Namespace) -> int:
        """
        Główna metoda uruchamiająca operacje OSINT.
        
        Args:
            args: Przetworzone argumenty wiersza poleceń.
            
        Returns:
            Kod wyjścia (0 dla sukcesu, inaczej dla błędu).
        """
        self.logger.info("Uruchomiono OSINT Super Kombajn", 
                         version=__version__, 
                         python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        
        # Przygotowanie zadań
        batch = {}
        task_id = 1
        
        if args.username:
            batch[f"sherlock_{task_id}"] = ("sherlock", args.username, self.results_dir / f"sherlock_{args.username}.json")
            task_id += 1
            batch[f"maigret_{task_id}"] = ("maigret", args.username, self.results_dir / f"maigret_{args.username}.json")
            task_id += 1
            
        if args.phone:
            batch[f"phoneinfoga_{task_id}"] = ("phoneinfoga", args.phone, self.results_dir / f"phoneinfoga_{args.phone.replace('+', '')}.json")
            task_id += 1
            
        if args.email:
            batch[f"holehe_{task_id}"] = ("holehe", args.email, self.results_dir / f"holehe_{args.email.replace('@', '_')}.json")
            task_id += 1
            
        if args.file:
            file_path = Path(args.file)
            batch[f"exiftool_{task_id}"] = ("exiftool", str(file_path), self.results_dir / f"exiftool_{file_path.name}.json")
            task_id += 1
            
        if not batch:
            self.logger.error("Nie określono żadnych danych wejściowych (--username, --phone, --email, --file)")
            return 1

        # Wykonanie zadań
        self.logger.info(f"Zaplanowano {len(batch)} zadań do wykonania")
        results = await self.run_batch(batch)
        
        # Analiza AI (jeśli włączona)
        ai_enabled = self.config.get("api", {}).get("ai", {}).get("enabled", False)
        ai_result = None
        
        if ai_enabled and args.analyze:
            successful_results = [r for r in results if r.get("success", False)]
            if successful_results:
                self.logger.info("Uruchamianie analizy AI")
                ai_output_path = self.results_dir / f"ai_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                ai_result = await analyze_results(successful_results, ai_output_path)
                if ai_result.get("success", False):
                    self.logger.info("Analiza AI zakończona pomyślnie", output_path=str(ai_output_path))
                else:
                    self.logger.error(f"Analiza AI nie powiodła się: {ai_result.get('error')}")
            else:
                self.logger.warning("Brak pomyślnych wyników do analizy AI")
        
        # Generowanie raportu
        if args.report:
            self.logger.info("Generowanie raportu")
            report_path = self.results_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "version": __version__,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "target": args.username or args.phone or args.email or (args.file and Path(args.file).name)
            }
            
            # Dodaj analizę AI do raportu, jeśli dostępna
            if ai_result and ai_result.get("success", False):
                metadata["ai_analysis"] = ai_result.get("analysis", {})
                
            report_result = self.report_generator.generate_report(
                results=results,
                output_path=report_path,
                format=args.report_format,
                metadata=metadata
            )
            
            if report_result.get("success", False):
                self.logger.info("Raport wygenerowany pomyślnie", path=report_result.get("path"))
            else:
                self.logger.error(f"Generowanie raportu nie powiodło się: {report_result.get('error')}")
        
        # Zapisz metryki
        self.metrics.log_metrics()
        
        # Wyświetl podsumowanie
        success_count = sum(1 for r in results if r.get("success", False))
        print("\n" + "=" * 60)
        print("PODSUMOWANIE WYKONANIA NARZĘDZI OSINT")
        print("=" * 60)
        for result in results:
            tool = result.get("tool", "unknown")
            status = "✅ SUKCES" if result.get("success", False) else "❌ BŁĄD"
            print(f"{tool.upper()}: {status}")
            if result.get("output_path"):
                print(f"  Wyjście: {result['output_path']}")
            elif result.get("error"):
                print(f"  Błąd: {result['error']}")
        print(f"\nSukces: {success_count}/{len(results)}")
        print(f"Katalog wyników: {self.results_dir}")
        print("=" * 60)

        self.logger.info(f"Wykonano {success_count}/{len(results)} narzędzi pomyślnie")
        return 0 if success_count > 0 else 1


def parse_arguments() -> argparse.Namespace:
    """Parsuje argumenty wiersza poleceń."""
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
    mode_group.add_argument("--analyze", action="store_true", help="Uruchom analizę AI wyników")
    
    # Raportowanie
    report_group = parser.add_argument_group("Raportowanie")
    report_group.add_argument("--report", action="store_true", help="Generuj raport z wyników")
    report_group.add_argument("--report-format", type=str, choices=["html", "json", "txt", "pdf"], default="html", help="Format raportu")
    
    # Konfiguracja
    config_group = parser.add_argument_group("Konfiguracja")
    config_group.add_argument("--config", type=str, help="Ścieżka do pliku konfiguracyjnego")
    config_group.add_argument("--output-dir", type=str, help="Katalog dla plików wyjściowych")
    config_group.add_argument("--verbose", "-v", action="store_true", help="Tryb szczegółowego logowania")
    
    return parser.parse_args()


async def run_app() -> int:
    """Główna funkcja uruchamiająca aplikację."""
    args = parse_arguments()
    
    try:
        suite = OSINTSuite(
            config_file=Path(args.config) if args.config else None,
            results_dir=Path(args.output_dir) if args.output_dir else None,
            verbose=args.verbose
        )
        return await suite.main(args)
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