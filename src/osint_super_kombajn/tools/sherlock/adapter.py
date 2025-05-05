"""
Adapter dla narzędzia Sherlock.
"""
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from osint_super_kombajn.config import config

class SherlockAdapter:
    """
    Adapter dla narzędzia Sherlock do wyszukiwania kont użytkowników.
    """
    
    def __init__(self):
        """Inicjalizuje adapter Sherlock."""
        self.sherlock_path = config["tools"]["sherlock"]["path"]
        self.timeout = config["tools"]["sherlock"]["timeout"]
    
    def search(self, username: str) -> Dict[str, Any]:
        """
        Wyszukuje konta użytkownika na różnych platformach.
        
        Args:
            username: Nazwa użytkownika do wyszukania
            
        Returns:
            Wyniki wyszukiwania
        """
        # W rzeczywistej implementacji, wywołalibyśmy tutaj Sherlock
        # Dla celów demonstracyjnych, zwracamy przykładowe dane
        return {
            "found": ["twitter", "github", "reddit", "instagram"],
            "not_found": ["facebook", "linkedin", "pinterest"],
            "error": []
        }
    
    def _run_sherlock(self, username: str) -> Dict[str, Any]:
        """
        Uruchamia narzędzie Sherlock.
        
        Args:
            username: Nazwa użytkownika do wyszukania
            
        Returns:
            Wyniki wyszukiwania
        """
        # Ta metoda byłaby używana w rzeczywistej implementacji
        # Dla celów demonstracyjnych, nie jest używana
        try:
            # Przykładowe wywołanie Sherlock
            result = subprocess.run(
                [
                    "python", 
                    "-m", 
                    "sherlock", 
                    username, 
                    "--output", 
                    "json"
                ],
                cwd=self.sherlock_path,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                # Parsowanie wyników
                return json.loads(result.stdout)
            else:
                return {
                    "found": [],
                    "not_found": [],
                    "error": [f"Błąd wykonania Sherlock: {result.stderr}"]
                }
                
        except subprocess.TimeoutExpired:
            return {
                "found": [],
                "not_found": [],
                "error": ["Przekroczono limit czasu wykonania"]
            }
        except Exception as e:
            return {
                "found": [],
                "not_found": [],
                "error": [f"Błąd: {str(e)}"]
            }
