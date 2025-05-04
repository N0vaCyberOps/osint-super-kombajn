"""
Moduł zawierający implementację wzorca Command dla narzędzi OSINT Super Kombajn.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Protocol, Type, TypeVar
import functools

T = TypeVar('T', bound='OSINTCommand')


class OSINTCommand(ABC):
    """Abstrakcyjna klasa bazowa dla wzorca Command narzędzi OSINT."""
    
    tool_name: str = "unknown"
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Wykonuje komendę narzędzia OSINT.
        
        Returns:
            Wynik wykonania komendy.
        """
        pass


class ToolRegistry:
    """Rejestr narzędzi OSINT wykorzystujący wzorzec Command."""
    
    def __init__(self):
        """Inicjalizuje rejestr narzędzi."""
        self._tools: Dict[str, OSINTCommand] = {}
        
    def register(self, name: str, command: OSINTCommand) -> None:
        """
        Rejestruje nowe narzędzie.
        
        Args:
            name: Nazwa narzędzia.
            command: Komenda narzędzia.
        """
        self._tools[name] = command
        
    def get(self, name: str) -> Optional[OSINTCommand]:
        """
        Pobiera zarejestrowane narzędzie.
        
        Args:
            name: Nazwa narzędzia.
            
        Returns:
            Komenda narzędzia lub None, jeśli narzędzie nie istnieje.
        """
        return self._tools.get(name)
    
    def get_all(self) -> Dict[str, OSINTCommand]:
        """
        Pobiera wszystkie zarejestrowane narzędzia.
        
        Returns:
            Słownik z wszystkimi zarejestrowanymi narzędziami.
        """
        return self._tools.copy()
    
    def is_registered(self, name: str) -> bool:
        """
        Sprawdza, czy narzędzie jest zarejestrowane.
        
        Args:
            name: Nazwa narzędzia.
            
        Returns:
            True jeśli narzędzie jest zarejestrowane, False w przeciwnym razie.
        """
        return name in self._tools