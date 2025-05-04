"""
Moduł zawierający bazową klasę adaptera dla narzędzi OSINT.
"""

import json
import asyncio
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Callable, TypeVar, Generic
from datetime import datetime

from ..core.command import OSINTCommand

T = TypeVar('T')  # Typ danych wejściowych
R = TypeVar('R')  # Typ wyniku


class BaseAdapter(OSINTCommand, Generic[T, R]):
    """Bazowa klasa adaptera dla narzędzi OSINT."""
    
    tool_name = "base"
    required_binaries: List[str] = []
    
    def __init__(self, timeout: int = 300, max_retries: int = 3):
        """
        Inicjalizuje bazowy adapter.

        Args:
            timeout: Limit czasu w sekundach dla wykonania.
            max_retries: Maksymalna liczba ponownych prób w przypadku błędu.
        """
        self.timeout = timeout
        self.max_retries = max_retries
    
    async def execute(self, input_data: T, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Wykonuje operację narzędzia OSINT.
        
        Args:
            input_data: Dane wejściowe dla narzędzia.
            output_path: Ścieżka do zapisania wyników.
            
        Returns:
            Wynik operacji.
        """
        raise NotImplementedError("Metoda execute musi być zaimplementowana w klasie potomnej")
    
    async def run_with_retries(
        self,
        operation: Callable[[], R],
        validate_result: Optional[Callable[[R], bool]] = None,
        error_message: str = "Operacja nie powiodła się"
    ) -> Tuple[bool, Optional[R], Optional[str]]:
        """
        Wykonuje operację z mechanizmem ponownych prób.
        
        Args:
            operation: Funkcja do wykonania.
            validate_result: Opcjonalna funkcja do walidacji wyniku.
            error_message: Komunikat błędu.
            
        Returns:
            Krotka (sukces, wynik, komunikat błędu).
        """
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                result = await asyncio.wait_for(operation(), timeout=self.timeout)
                
                # Jeśli nie ma funkcji walidacji lub walidacja przeszła pomyślnie
                if validate_result is None or validate_result(result):
                    return True, result, None
                
                # Jeśli walidacja nie przeszła
                last_error = "Walidacja wyniku nie powiodła się"
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
        
        return False, None, f"{error_message}. Ostatni błąd: {last_error}"
    
    async def run_command(
        self,
        cmd: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Wykonuje polecenie systemowe.
        
        Args:
            cmd: Lista argumentów polecenia.
            cwd: Katalog roboczy.
            env: Zmienne środowiskowe.
            
        Returns:
            Krotka (sukces, stdout, stderr).
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout)
            
            if process.returncode != 0:
                stderr_output = stderr.decode('utf-8', errors='replace')
                return False, None, stderr_output or f"Kod błędu: {process.returncode}"
                
            return True, stdout.decode('utf-8', errors='replace'), None
            
        except asyncio.TimeoutError:
            return False, None, f"Przekroczono limit czasu {self.timeout}s"
        except Exception as e:
            return False, None, str(e)
    
    def prepare_output_path(
        self,
        output_path: Optional[Path],
        prefix: str,
        identifier: str,
        suffix: str = ".json"
    ) -> Path:
        """
        Przygotowuje ścieżkę wyjściową.
        
        Args:
            output_path: Opcjonalna ścieżka wyjściowa.
            prefix: Prefiks dla nazwy pliku.
            identifier: Identyfikator dla nazwy pliku.
            suffix: Rozszerzenie pliku.
            
        Returns:
            Ścieżka wyjściowa.
        """
        if output_path is None:
            sanitized_id = identifier.replace('@', '_').replace('+', '').replace('/', '_')
            output_path = Path(f"results/{prefix}_{sanitized_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path
    
    def load_json_file(self, file_path: Path) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Ładuje plik JSON.
        
        Args:
            file_path: Ścieżka do pliku JSON.
            
        Returns:
            Krotka (sukces, dane, komunikat błędu).
        """
        try:
            if not file_path.exists():
                return False, None, f"Plik nie istnieje: {file_path}"
                
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            return True, data, None
        except json.JSONDecodeError as e:
            return False, None, f"Błąd dekodowania JSON: {e}"
        except Exception as e:
            return False, None, f"Błąd ładowania pliku: {e}"
    
    def save_json_file(self, file_path: Path, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Zapisuje dane do pliku JSON.
        
        Args:
            file_path: Ścieżka do pliku JSON.
            data: Dane do zapisania.
            
        Returns:
            Krotka (sukces, komunikat błędu).
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            return True, None
        except Exception as e:
            return False, f"Błąd zapisywania pliku: {e}"
