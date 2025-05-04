"""
Moduł zawierający implementację puli asynchronicznych pracowników dla równoległego wykonywania zadań.
"""

import asyncio
import functools
from typing import Dict, List, Any, Callable, TypeVar, Optional, Tuple, Set

T = TypeVar('T')


class AsyncWorkerPool:
    """Pula do zarządzania równoległymi zadaniami asynchronicznymi z ograniczeniami."""
    
    def __init__(self, max_workers: int = 5):
        """
        Inicjalizuje pulę pracowników.
        
        Args:
            max_workers: Maksymalna liczba równoległych zadań.
        """
        self.semaphore = asyncio.Semaphore(max_workers)
        self.tasks: List[asyncio.Task] = []
    
    async def submit(self, coro: Callable[..., T], *args, **kwargs) -> T:
        """
        Przesyła korutynę do puli.
        
        Args:
            coro: Korutyna do wykonania.
            *args: Argumenty do przekazania do korutyny.
            **kwargs: Argumenty słownikowe do przekazania do korutyny.
            
        Returns:
            Wynik wykonania korutyny.
        """
        async with self.semaphore:
            return await coro(*args, **kwargs)
    
    async def map(self, coro: Callable[[Any], T], items: List[Any]) -> List[T]:
        """
        Mapuje korutynę na listę elementów z ograniczeniem równoległości.
        
        Args:
            coro: Korutyna do wykonania na każdym elemencie.
            items: Lista elementów do przetworzenia.
            
        Returns:
            Lista wyników wykonania korutyny.
        """
        tasks = [self.submit(coro, item) for item in items]
        return await asyncio.gather(*tasks, return_exceptions=True)
        
    async def execute_batch(self, 
                           tasks: Dict[str, Callable[[], T]], 
                           on_result: Optional[Callable[[str, T], None]] = None) -> Dict[str, T]:
        """
        Wykonuje pakiet nazwanych zadań.
        
        Args:
            tasks: Słownik zadań w formacie {nazwa_zadania: korutyna}.
            on_result: Opcjonalna funkcja wywoływana po zakończeniu zadania.
            
        Returns:
            Słownik wyników w formacie {nazwa_zadania: wynik}.
        """
        async def _execute(name, task_fn):
            result = await self.submit(task_fn)
            if on_result:
                on_result(name, result)
            return name, result
        
        task_coros = [_execute(name, task_fn) for name, task_fn in tasks.items()]
        results = await asyncio.gather(*task_coros, return_exceptions=True)
        
        results_dict = {}
        for name_result in results:
            if isinstance(name_result, Exception):
                continue
            name, result = name_result
            results_dict[name] = result
            
        return results_dict
    
    async def execute_with_timeout(self, 
                                 coro: Callable[..., T], 
                                 timeout: float, 
                                 *args, 
                                 **kwargs) -> Tuple[bool, Optional[T], Optional[Exception]]:
        """
        Wykonuje korutynę z limitem czasu.
        
        Args:
            coro: Korutyna do wykonania.
            timeout: Limit czasu w sekundach.
            *args: Argumenty do przekazania do korutyny.
            **kwargs: Argumenty słownikowe do przekazania do korutyny.
            
        Returns:
            Krotka (sukces, wynik, wyjątek).
        """
        try:
            task = asyncio.create_task(coro(*args, **kwargs))
            self.tasks.append(task)
            
            try:
                result = await asyncio.wait_for(task, timeout)
                return True, result, None
            except asyncio.TimeoutError:
                if not task.done():
                    task.cancel()
                return False, None, asyncio.TimeoutError(f"Zadanie przekroczyło limit {timeout}s")
        except Exception as e:
            return False, None, e
        finally:
            if task in self.tasks:
                self.tasks.remove(task)