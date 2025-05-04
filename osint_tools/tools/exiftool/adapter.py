"""
Adapter dla narzędzia ExifTool do analizy metadanych plików.
"""

import json
import asyncio
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from ...utils.validators import validate_file
from ...core.command import OSINTCommand


class ExifToolAdapter(OSINTCommand):
    """Adapter do integracji z narzędziem ExifTool."""
    
    tool_name = "exiftool"
    required_binaries = ["exiftool"]
    
    def __init__(self, timeout: int = 300, max_retries: int = 3):
        """
        Inicjalizuje adapter ExifTool.

        Args:
            timeout: Limit czasu w sekundach dla analizy.
            max_retries: Maksymalna liczba ponownych prób w przypadku błędu.
        """
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Sprawdź, czy ExifTool jest dostępny
        try:
            result = subprocess.run(
                ["exiftool", "-ver"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                check=False
            )
            if result.returncode != 0:
                raise RuntimeError("ExifTool nie jest dostępny")
        except FileNotFoundError:
            raise RuntimeError("ExifTool nie jest zainstalowany")
            
    async def execute(self, file_path: str, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Wykonuje analizę ExifTool dla pliku.
        
        Args:
            file_path: Ścieżka do pliku do analizy.
            output_path: Ścieżka do zapisania wyników.
            
        Returns:
            Wynik analizy.
        """
        return await self.extract_metadata(Path(file_path), output_path)

    async def extract_metadata(self, file_path: Path, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Ekstrahuje metadane z pliku.

        Args:
            file_path: Ścieżka do pliku do analizy.
            output_path: Ścieżka do zapisania wyników.

        Returns:
            Słownik zawierający wyniki analizy.
        """
        # Walidacja pliku
        validation = validate_file(file_path)
        if validation is not True:
            return {"success": False, "error": validation, "file_path": str(file_path)}

        # Przygotuj ścieżkę wyjściową
        if output_path is None:
            output_path = Path(f"results/exiftool_{file_path.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Przygotuj dane do śledzenia ponownych prób
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                # Przygotuj polecenie ExifTool
                cmd = ["exiftool", "-j", "-g", "-a", "-u", str(file_path)]
                
                # Uruchom ExifTool
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
                    
                # Parsuj wyniki JSON
                try:
                    metadata = json.loads(stdout.decode('utf-8'))
                    
                    # ExifTool zwraca zawsze listę, weź pierwszy element
                    if isinstance(metadata, list) and len(metadata) > 0:
                        metadata = metadata[0]
                        
                    # Zapisz wyniki do pliku wyjściowego
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(metadata, f, indent=2, ensure_ascii=False)
                        
                    return {
                        "success": True, 
                        "data": metadata, 
                        "file_path": str(file_path), 
                        "output_path": str(output_path),
                        "metadata_groups": len(metadata)
                    }
                except json.JSONDecodeError as e:
                    last_error = f"Błąd dekodowania JSON: {e}"
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
            "file_path": str(file_path),
            "retry_count": retry_count
        }