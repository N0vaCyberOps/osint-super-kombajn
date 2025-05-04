"""
Adapter dla narzędzia Maigret do wyszukiwania profili użytkowników.
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import functools

from ...utils.validators import validate_username, sanitize_command_input
from ...core.base_adapter import BaseAdapter


class MaigretAdapter(BaseAdapter[str, Dict[str, Any]]):
    """Adapter do integracji z narzędziem Maigret."""
    
    tool_name = "maigret"
    required_binaries = ["python"]
    
    def __init__(self, maigret_path: Optional[Path] = None, timeout: int = 300, max_retries: int = 3):
        """
        Inicjalizuje adapter Maigret.

        Args:
            maigret_path: Ścieżka do instalacji Maigret. Jeśli None, używa domyślnej.
            timeout: Limit czasu w sekundach dla wyszukiwania.
            max_retries: Maksymalna liczba ponownych prób w przypadku błędu.
        """
        super().__init__(timeout=timeout, max_retries=max_retries)
        self.maigret_path = maigret_path or Path("./tools/maigret")
        
        # Sprawdź, czy ścieżka Maigret istnieje
        if not self.maigret_path.exists():
            raise FileNotFoundError(f"Ścieżka Maigret nie istnieje: {self.maigret_path}")
            
        # Sprawdź, czy skrypt Maigret istnieje
        maigret_script = self.maigret_path / "maigret.py"
        if not maigret_script.exists():
            raise FileNotFoundError(f"Skrypt Maigret nie istnieje: {maigret_script}")
            
    async def execute(self, username: str, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Wykonuje wyszukiwanie Maigret dla nazwy użytkownika.
        
        Args:
            username: Nazwa użytkownika do wyszukania.
            output_path: Ścieżka do zapisania wyników.
            
        Returns:
            Wynik wyszukiwania.
        """
        return await self.search_username(username, output_path)

    async def search_username(self, username: str, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Wyszukuje nazwę użytkownika na różnych platformach.

        Args:
            username: Nazwa użytkownika do wyszukania.
            output_path: Ścieżka do zapisania wyników.

        Returns:
            Słownik zawierający wyniki wyszukiwania.
        """
        # Walidacja nazwy użytkownika
        validation = validate_username(username)
        if validation is not True:
            return {"success": False, "error": validation, "username": username}
            
        # Sanityzacja nazwy użytkownika
        username = sanitize_command_input(username)

        # Przygotuj ścieżkę wyjściową
        output_path = self.prepare_output_path(output_path, "maigret", username)
        
        # Funkcja do wykonania wyszukiwania
        async def run_search():
            cmd = [
                "python", str(self.maigret_path / "maigret.py"), 
                username, "--json", str(output_path)
            ]
            
            success, stdout, stderr = await self.run_command(
                cmd=cmd,
                cwd=str(self.maigret_path)
            )
            
            if not success:
                return None
                
            # Sprawdź, czy plik wyjściowy został utworzony
            success, data, error = self.load_json_file(output_path)
            if not success:
                return None
                
            # Przygotuj podsumowanie (ilość znalezionych serwisów)
            found_services = [service for service in data if service.get("status", "") == "found"]
            results_summary = {
                "username": username,
                "total_services": len(data),
                "found_services": len(found_services),
                "services": data
            }
            
            # Zapisz podsumowanie do pliku
            success, error = self.save_json_file(output_path, results_summary)
            if not success:
                return None
                
            return results_summary
        
        # Wykonaj wyszukiwanie z mechanizmem ponownych prób
        success, result, error = await self.run_with_retries(
            operation=run_search,
            error_message="Wyszukiwanie Maigret nie powiodło się"
        )
        
        if success and result:
            return {
                "success": True, 
                "data": result, 
                "username": username, 
                "output_path": str(output_path),
                "found_count": result.get("found_services", 0)
            }
        else:
            return {
                "success": False, 
                "error": error, 
                "username": username,
                "retry_count": self.max_retries
            }
