"""
Moduł szyny zdarzeń dla OSINT Super Kombajn.
"""
import asyncio
from typing import Dict, List, Any, Callable, Awaitable, Optional

class EventBus:
    """
    Szyna zdarzeń do komunikacji między komponentami.
    
    Umożliwia publikowanie i subskrybowanie zdarzeń w systemie.
    """
    
    def __init__(self):
        """Inicjalizuje szynę zdarzeń."""
        self.subscribers: Dict[str, List[Callable[[Dict[str, Any]], Awaitable[None]]]] = {}
    
    def subscribe(self, event_type: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        """
        Dodaje subskrybenta dla określonego typu zdarzenia.
        
        Args:
            event_type: Typ zdarzenia do subskrypcji
            callback: Funkcja wywoływana przy wystąpieniu zdarzenia
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(callback)
    
    async def publish(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Publikuje zdarzenie określonego typu.
        
        Args:
            event_type: Typ publikowanego zdarzenia
            data: Dane związane ze zdarzeniem
        """
        if data is None:
            data = {}
        
        if event_type in self.subscribers:
            tasks = [callback(data) for callback in self.subscribers[event_type]]
            await asyncio.gather(*tasks)
    
    def unsubscribe(self, event_type: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        """
        Usuwa subskrybenta dla określonego typu zdarzenia.
        
        Args:
            event_type: Typ zdarzenia
            callback: Funkcja do usunięcia z listy subskrybentów
        """
        if event_type in self.subscribers and callback in self.subscribers[event_type]:
            self.subscribers[event_type].remove(callback)

# Globalna instancja szyny zdarzeń
event_bus = EventBus()
