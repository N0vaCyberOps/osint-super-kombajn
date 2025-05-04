"""
Adapter dla narzędzia Maigret do wyszukiwania profili użytkowników.
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from ...utils.validators import validate_username, sanitize_command_input
from ...core.command import OSINTCommand


class MaigretAdapter(OSINTCommand):
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
        self.maigret_path = maigret_path or Path("./tools/maigret")
        self.timeout = timeout
        self.max_retries = max_retries
        
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
        if output_path is Non