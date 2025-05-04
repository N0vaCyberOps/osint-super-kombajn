"""
Moduł zawierający narzędzia do zbierania metryk dla OSINT Super Kombajn.
"""

import time
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path


@dataclass
class ToolMetrics:
    """Kolekcja metryk dla wykonania narzędzia."""
    
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_duration_ms: float = 0
    execution_times_ms: List[float] = field(default_factory=list)
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    
    def record_execution(self, success: bool, duration_ms: float, error_type: Optional[str] = None) -> None:
        """
        Rejestruje wykonanie narzędzia.
        
        Args:
            success: Czy wykonanie zakończyło się sukcesem.
            duration_ms: Czas wykonania w milisekundach.
            error_type: Typ błędu, jeśli wystąpił.
        """
        self.total_executions += 1
        if success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1
            if error_type:
                self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1
        
        self.total_duration_ms += duration_ms
        self.execution_times_ms.append(duration_ms)
    
    @property
    def average_duration_ms(self) -> float:
        """
        Pobiera średni czas wykonania w milisekundach.
        
        Returns:
            Średni czas wykonania w milisekundach.
        """
        if not self.total_executions:
            return 0
        return self.total_duration_ms / self.total_executions
    
    @property
    def success_rate(self) -> float:
        """
        Pobiera współczynnik sukcesu jako procent.
        
        Returns:
            Współczynnik sukcesu jako procent.
        """
        if not self.total_executions:
            return 0
        return (self.successful_executions / self.total_executions) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Konwertuje metryki na słownik.
        
        Returns:
            Słownik z metrykami.
        """
        return {
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "success_rate_percent": round(self.success_rate, 2),
            "average_duration_ms": round(self.average_duration_ms, 2),
            "total_duration_ms": round(self.total_duration_ms, 2),
            "errors_by_type": self.errors_by_type
        }


class MetricsCollector:
    """Kolektor metryk aplikacji."""
    
    def __init__(self, log_dir: Optional[Path] = None):
        """
        Inicjalizuje kolektor metryk.
        
        Args:
            log_dir: Katalog do zapisywania plików metryk.
        """
        self.start_time = time.time()
        self.metrics_by_tool: Dict[str, ToolMetrics] = {}
        self.log_dir = log_dir or Path("./metrics")
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def get_tool_metrics(self, tool_name: str) -> ToolMetrics:
        """
        Pobiera lub tworzy metryki dla narzędzia.
        
        Args:
            tool_name: Nazwa narzędzia.
            
        Returns:
            Metryki narzędzia.
        """
        if tool_name not in self.metrics_by_tool:
            self.metrics_by_tool[tool_name] = ToolMetrics()
        return self.metrics_by_tool[tool_name]
    
    def record_tool_execution(self, 
                             tool_name: str, 
                             success: bool, 
                             start_time: float, 
                             error_type: Optional[str] = None) -> None:
        """
        Rejestruje wykonanie narzędzia z pomiarem czasu.
        
        Args:
            tool_name: Nazwa narzędzia.
            success: Czy wykonanie zakończyło się sukcesem.
            start_time: Czas rozpoczęcia wykonania (znacznik czasu).
            error_type: Typ błędu, jeśli wystąpił.
        """
        duration_ms = (time.time() - start_time) * 1000
        metrics = self.get_tool_metrics(tool_name)
        metrics.record_execution(success, duration_ms, error_type)
    
    @property
    def uptime_seconds(self) -> float:
        """
        Pobiera czas działania aplikacji w sekundach.
        
        Returns:
            Czas działania aplikacji w sekundach.
        """
        return time.time() - self.start_time
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Pobiera wszystkie zebrane metryki.
        
        Returns:
            Słownik z wszystkimi metrykami.
        """
        return {
            "uptime_seconds": round(self.uptime_seconds, 2),
            "total_tools": len(self.metrics_by_tool),
            "tools": {name: metrics.to_dict() for name, metrics in self.metrics_by_tool.items()}
        }
    
    def log_metrics(self) -> None:
        """Zapisuje aktualne metryki do pliku."""
        metrics_file = self.log_dir / f"metrics_{datetime.now().strftime('%Y%m%d')}.json"
        try:
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(self.get_all_metrics(), f, indent=2, ensure_ascii=False)
        except IOError as e:
            logging.error(f"Nie udało się zapisać metryk do {metrics_file}: {e}")