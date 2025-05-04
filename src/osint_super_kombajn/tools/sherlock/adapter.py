# src/osint_super_kombajn/tools/sherlock/adapter.py
"""
Adapter dla narzędzia Sherlock do wyszukiwania profili użytkowników w mediach społecznościowych.
"""

import json
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional

class SherlockAdapter:
    """
    Adapter do integracji z narzędziem Sherlock.
    
    Sherlock to narzędzie Python umożliwiające wyszukiwanie nazw użytkowników 
    na wielu platformach społecznościowych.
    """
    
    def __init__(self, sherlock_path: Optional[Path] = None, timeout: int = 300):
        """
        Inicjalizacja adaptera Sherlock.
        
        Args:
            sherlock_path: Ścieżka do instalacji Sherlock. Jeśli None, używa domyślnej.
            timeout: Limit czasu w sekundach dla pojedynczego wyszukiwania.
        """
        self.sherlock_path = sherlock_path or Path("./tools/sherlock")
        self.timeout = timeout
    
    async def search_username(self, username: str, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Wyszukuje nazwę użytkownika na różnych platformach.
        
        Args:
            username: Nazwa użytkownika do wyszukania
            output_path: Opcjonalna ścieżka do zapisania wyników. Jeśli None, używa tymczasowego pliku.
            
        Returns:
            Słownik zawierający wyniki wyszukiwania
        """
        # Określ plik wyjściowy
        if output_path is None:
            output_path = Path(f"./results/sherlock_{username}.json")
        
        # Przygotuj argumenty
        sherlock_script = self.sherlock_path / "sherlock.py"
        cmd = [
            "python", 
            str(sherlock_script),
            username,
            "--json",
            str(output_path),
            "--timeout", 
            str(self.timeout)
        ]
        
        try:
            # Uruchom Sherlock
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Sprawdź błąd
            if process.returncode != 0:
                return {
                    "success": False,
                    "error": stderr.decode() if stderr else f"Process returned code {process.returncode}",
                    "username": username
                }
            
            # Wczytaj wyniki
            if output_path.exists():
                with open(output_path, "r") as f:
                    results = json.load(f)
                return {
                    "success": True,
                    "data": results,
                    "username": username
                }
            else:
                return {
                    "success": False,
                    "error": "Output file not created",
                    "username": username
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "username": username
            }