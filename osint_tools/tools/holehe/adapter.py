"""
Adapter dla narzędzia Holehe do weryfikacji adresów e-mail.
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from ...utils.validators import validate_email, sanitize_command_input
from ...core.command import OSINTCommand


class HoleheAdapter(OSINTCommand):
    """Adapter do integracji z narzędziem Holehe."""
    
    tool_name = "holehe"
    required_binaries = ["python"]
    
    def __init__(self, holehe_path: Optional[Path] = None, timeout: int = 300, max_retries: int = 3):
        """
        Inicjalizuje adapter Holehe.

        Args:
            holehe_path: Ścieżka do instalacji Holehe. Jeśli None, używa domyślnej.
            timeout: Limit czasu w sekundach dla wyszukiwania.
            max_retries: Maksymalna liczba ponownych prób w przypadku błędu.
        """
        self.holehe_path = holehe_path or Path("./tools/holehe")
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Sprawdź, czy ścieżka Holehe istnieje
        if not self.holehe_path.exists():
            raise FileNotFoundError(f"Ścieżka Holehe nie istnieje: {self.holehe_path}")
            
        # Sprawdź, czy główny skrypt Holehe istnieje
        holehe_script = self.holehe_path / "holehe.py"
        if not holehe_script.exists():
            raise FileNotFoundError(f"Skrypt Holehe nie istnieje: {holehe_script}")
            
    async def execute(self, email: str, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Wykonuje sprawdzenie Holehe dla adresu e-mail.
        
        Args:
            email: Adres e-mail do sprawdzenia.
            output_path: Ścieżka do zapisania wyników.
            
        Returns:
            Wynik sprawdzenia.
        """
        return await self.check_email(email, output_path)

    async def check_email(self, email: str, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Sprawdza adres e-mail na różnych platformach.

        Args:
            email: Adres e-mail do sprawdzenia.
            output_path: Ścieżka do zapisania wyników.

        Returns:
            Słownik zawierający wyniki analizy.
        """
        # Walidacja adresu e-mail
        validation = validate_email(email)
        if validation is not True:
            return {"success": False, "error": validation, "email": email}
            
        # Sanityzacja adresu e-mail
        email = sanitize_command_input(email)

        # Przygotuj ścieżkę wyjściową
        if output_path is None:
            output_path = Path(f"results/holehe_{email.replace('@', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Przygotuj dane do śledzenia ponownych prób
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                # Przygotuj polecenie Holehe
                cmd = [
                    "python", str(self.holehe_path / "holehe.py"), 
                    email, "--json", str(output_path)
                ]
                
                # Uruchom Holehe
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(self.holehe_path)
                )
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout)
                
                if process.returncode != 0:
                    stderr_output = stderr.decode('utf-8', errors='replace')
                    # Jeśli to błąd, zapisz i spróbuj ponownie
                    last_error = stderr_output or f"Kod błędu: {process.returncode}"
                    retry_count += 1
                    continue
                    
                # Sprawdź, czy plik wyjściowy został utworzony
                if output_path.exists():
                    try:
                        with open(output_path, "r", encoding="utf-8") as f:
                            results = json.load(f)
                            
                        # Przygotuj podsumowanie (ilość znalezionych serwisów)
                        found_services = [service for service in results if service.get("exists", False)]
                        results_summary = {
                            "email": email,
                            "total_services": len(results),
                            "found_services": len(found_services),
                            "services": results
                        }
                        
                        # Zapisz podsumowanie do pliku
                        with open(output_path, "w", encoding="utf-8") as f:
                            json.dump(results_summary, f, indent=2, ensure_ascii=False)
                            
                        return {
                            "success": True, 
                            "data": results_summary, 
                            "email": email, 
                            "output_path": str(output_path),
                            "found_count": len(found_services)
                        }
                    except json.JSONDecodeError as e:
                        last_error = f"Błąd dekodowania JSON: {e}"
                        retry_count += 1
                        continue
                else:
                    last_error = "Plik wyjściowy nie został utworzony"
                    retry_count += 1
                    continue
            except asyncio.TimeoutError:
                last_error = f"Przekroczono limit czasu {self.timeout}s"
                retry_count += 1
                continue
            except Exception as e:
                last_error = str(e)
                retry_count += 1
                continue
                
        # Jeśli dotarliśmy tutaj, wszystkie próby się nie powiodły
        return {
            "success": False, 
            "error": f"Wszystkie próby nie powiodły się. Ostatni błąd: {last_error}", 
            "email": email,
            "retry_count": retry_count
        }