"""
Moduł silnika OSINT Super Kombajn. Zarządza integracjami z narzędziami OSINT
i koordynuje ich wywołania.
"""

import os
import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from ..tools.sherlock.adapter import SherlockAdapter
from ..tools.phoneinfoga.adapter import PhoneInfogaAdapter
from ..tools.maigret.adapter import MaigretAdapter
from ..tools.exiftool.adapter import ExifToolAdapter
from ..tools.holehe.adapter import HoleheAdapter
from ..utils.logger import OSINTLogger


class OSINTEngine:
    """Główny silnik koordynujący działanie narzędzi OSINT."""
    
    def __init__(
        self,
        base_dir: Optional[Path] = None,
        log_dir: Optional[Path] = None,
        results_dir: Optional[Path] = None,
        config_file: Optional[Path] = None,
        verbose: bool = False
    ):
        """
        Inicjalizuje silnik OSINT.
        
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
        self.verbose = verbose
        
        # Tworzenie katalogów
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicjalizacja loggera
        log_level = "DEBUG" if verbose else "INFO"
        self.logger = OSINTLogger(
            log_dir=self.log_dir, 
            level=log_level,
            app_name="osint_engine",
            log_format="json"
        )
        
        # Inicjalizacja adapterów
        self.sherlock_adapter = SherlockAdapter(sherlock_path=self.base_dir / "sherlock", timeout=300)
        self.phoneinfoga_adapter = PhoneInfogaAdapter(timeout=300)
        self.maigret_adapter = MaigretAdapter(maigret_path=self.base_dir / "maigret", timeout=300)
        self.exiftool_adapter = ExifToolAdapter(timeout=300)
        self.holehe_adapter = HoleheAdapter(holehe_path=self.base_dir / "holehe", timeout=300)
        
        self.logger.info("OSINTEngine zainicjalizowany", base_dir=str(self.base_dir))
    
    async def run_all(
        self, 
        email: Optional[str] = None, 
        username: Optional[str] = None, 
        phone: Optional[str] = None, 
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Uruchamia wszystkie dostępne narzędzia OSINT dla podanych danych wejściowych.
        
        Args:
            email: Adres e-mail do analizy.
            username: Nazwa użytkownika do analizy.
            phone: Numer telefonu do analizy.
            file_path: Ścieżka do pliku do analizy.
            
        Returns:
            Słownik zawierający wyniki z wszystkich uruchomionych narzędzi.
        """
        self.logger.info("Uruchamianie wszystkich narzędzi OSINT", 
                         email=email, 
                         username=username, 
                         phone=phone, 
                         file_path=file_path)
        
        results = {}
        tasks = []
        
        # Przygotowanie zadań na podstawie danych wejściowych
        if username:
            sherlock_output_path = self.results_dir / f"sherlock_{username}.json"
            maigret_output_path = self.results_dir / f"maigret_{username}.json"
            
            tasks.append(("sherlock", self.sherlock_adapter.search_username(username, sherlock_output_path)))
            tasks.append(("maigret", self.maigret_adapter.search_username(username, maigret_output_path)))
        
        if phone:
            phoneinfoga_output_path = self.results_dir / f"phoneinfoga_{phone.replace('+', '')}.json"
            tasks.append(("phoneinfoga", self.phoneinfoga_adapter.scan_number(phone, phoneinfoga_output_path)))
        
        if email:
            holehe_output_path = self.results_dir / f"holehe_{email.replace('@', '_')}.json"
            tasks.append(("holehe", self.holehe_adapter.check_email(email, holehe_output_path)))
        
        if file_path:
            file_path_obj = Path(file_path)
            exiftool_output_path = self.results_dir / f"exiftool_{file_path_obj.name}.json"
            tasks.append(("exiftool", self.exiftool_adapter.extract_metadata(file_path_obj, exiftool_output_path)))
        
        # Uruchomienie zadań współbieżnie
        if tasks:
            for name, coro in tasks:
                try:
                    result = await coro
                    results[name] = result
                except Exception as e:
                    self.logger.error(f"Błąd podczas wykonywania {name}: {e}")
                    results[name] = {"success": False, "error": str(e)}
        
        self.logger.info(f"Zakończono wykonywanie {len(tasks)} narzędzi OSINT")
        return results
    
    def print_summary(self, results: Dict[str, Any]) -> None:
        """
        Wyświetla podsumowanie wyników.
        
        Args:
            results: Słownik z wynikami z narzędzi OSINT.
        """
        print("\n" + "=" * 60)
        print("PODSUMOWANIE WYKONANIA NARZĘDZI OSINT")
        print("=" * 60)
        
        success_count = 0
        for tool_name, result in results.items():
            status = "✅ SUKCES" if result.get("success", False) else "❌ BŁĄD"
            if result.get("success", False):
                success_count += 1
                
            print(f"{tool_name.upper()}: {status}")
            
            if result.get("output_path"):
                print(f"  Wyjście: {result['output_path']}")
            elif result.get("error"):
                print(f"  Błąd: {result['error']}")
                
            # Wyświetl dodatkowe informacje dla konkretnych narzędzi
            if tool_name == "sherlock" or tool_name == "maigret" and result.get("success", False):
                print(f"  Znalezione profile: {result.get('found_count', 0)}")
            elif tool_name == "holehe" and result.get("success", False):
                print(f"  Znalezione serwisy: {result.get('found_count', 0)}")
                
        print(f"\nSukces: {success_count}/{len(results)}")
        print(f"Katalog wyników: {self.results_dir}")
        print("=" * 60)
    
    def save_html_report(self, results: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """
        Zapisuje raport HTML z wynikami.
        
        Args:
            results: Słownik z wynikami z narzędzi OSINT.
            output_file: Ścieżka do pliku wyjściowego. Jeśli None, używa domyślnej.
            
        Returns:
            Ścieżka do wygenerowanego raportu.
        """
        if output_file is None:
            output_file = str(self.results_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        
        self.logger.info(f"Generowanie raportu HTML: {output_file}")
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>OSINT Super Kombajn - Raport</title>
                <meta charset="UTF-8">
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
                    h2 { color: #2980b9; }
                    .tool { margin-bottom: 30px; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
                    .success { color: green; }
                    .error { color: red; }
                    pre { background: #f8f9fa; padding: 10px; border-radius: 3px; overflow: auto; }
                    .metadata { color: #7f8c8d; font-size: 0.9em; }
                </style>
            </head>
            <body>
                <h1>OSINT Super Kombajn - Raport</h1>
                <div class="metadata">
                    <p>Data wygenerowania: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
                </div>
            """)
            
            for tool_name, result in results.items():
                status_class = "success" if result.get("success", False) else "error"
                status_text = "SUKCES" if result.get("success", False) else "BŁĄD"
                
                f.write(f"""
                <div class="tool">
                    <h2>{tool_name.upper()} <span class="{status_class}">[{status_text}]</span></h2>
                """)
                
                if result.get("success", False):
                    if "data" in result:
                        import json
                        data_json = json.dumps(result["data"], indent=4, ensure_ascii=False)
                        f.write(f"<pre>{data_json}</pre>")
                    
                    if "output_path" in result:
                        f.write(f"<p>Plik wyjściowy: {result['output_path']}</p>")
                        
                    if "found_count" in result:
                        f.write(f"<p>Znalezione elementy: {result['found_count']}</p>")
                else:
                    if "error" in result:
                        f.write(f"<p class='error'>Błąd: {result['error']}</p>")
                
                f.write("</div>")
            
            f.write("""
            </body>
            </html>
            """)
        
        self.logger.info(f"Raport HTML wygenerowany: {output_file}")
        return output_file