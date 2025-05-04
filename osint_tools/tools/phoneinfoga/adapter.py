"""
Adapter dla narzędzia PhoneInfoga do analizy numerów telefonów.
"""

import json
import asyncio
import tempfile
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from ...utils.validators import validate_phone, sanitize_command_input
from ...core.command import OSINTCommand


class PhoneInfogaAdapter(OSINTCommand):
    """Adapter do integracji z narzędziem PhoneInfoga."""
    
    tool_name = "phoneinfoga"
    required_binaries = ["docker"]
    
    def __init__(self, timeout: int = 300, max_retries: int = 3):
        """
        Inicjalizuje adapter PhoneInfoga.

        Args:
            timeout: Limit czasu w sekundach dla wyszukiwania.
            max_retries: Maksymalna liczba ponownych prób w przypadku błędu.
        """
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Sprawdź, czy Docker jest dostępny
        try:
            result = subprocess.run(
                ["docker", "info"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                check=False
            )
            if result.returncode != 0:
                raise RuntimeError("Docker nie jest dostępny")
        except FileNotFoundError:
            raise RuntimeError("Docker nie jest zainstalowany")
            
    async def execute(self, phone_number: str, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Wykonuje skanowanie PhoneInfoga dla numeru telefonu.
        
        Args:
            phone_number: Numer telefonu do analizy.
            output_path: Ścieżka do zapisania wyników.
            
        Returns:
            Wynik skanowania.
        """
        return await self.scan_number(phone_number, output_path)

    async def scan_number(self, phone_number: str, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Skanuje numer telefonu w poszukiwaniu informacji.

        Args:
            phone_number: Numer telefonu do analizy.
            output_path: Ścieżka do zapisania wyników.

        Returns:
            Słownik zawierający wyniki skanowania.
        """
        # Walidacja numeru telefonu
        validation = validate_phone(phone_number)
        if validation is not True:
            return {"success": False, "error": validation, "phone_number": phone_number}
            
        # Sanityzacja numeru telefonu
        phone_number = sanitize_command_input(phone_number)

        # Przygotuj ścieżkę wyjściową
        if output_path is None:
            output_path = Path(f"results/phoneinfoga_{phone_number.replace('+', '')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Przygotuj dane do śledzenia ponownych prób
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_output = Path(temp_dir) / "output.json"
                    
                    # Przygotuj polecenie PhoneInfoga
                    cmd = [
                        "docker", "run", "--rm", 
                        "-v", f"{temp_dir}:/output",
                        "sundowndev/phoneinfoga", "scan",
                        "-n", phone_number, 
                        "--output", "/output/output.json", 
                        "--format", "json"
                    ]
                    
                    # Uruchom PhoneInfoga
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout)
                    
                    if process.returncode != 0:
                        stderr_output = stderr.decode('utf-8', errors='replace')
                        # Jeśli to błąd, zapisz i spróbuj ponownie
                        last_error = stderr_output or f"Kod błędu: {process.returncode}"
                        retry_count += 1
                        continue
                        
                    temp_output_path = Path(temp_dir) / "output.json"
                    if temp_output_path.exists():
                        try:
                            with open(temp_output_path, "r", encoding="utf-8") as f:
                                results = json.load(f)
                                
                            # Zapisz wyniki do docelowego pliku
                            with open(output_path, "w", encoding="utf-8") as f:
                                json.dump(results, f, indent=2, ensure_ascii=False)
                                
                            return {
                                "success": True, 
                                "data": results, 
                                "phone_number": phone_number, 
                                "output_path": str(output_path)
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
            "phone_number": phone_number,
            "retry_count": retry_count
        }