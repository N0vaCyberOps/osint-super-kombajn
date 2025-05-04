"""
Moduł zawierający narzędzia logowania dla OSINT Super Kombajn.
"""

import logging
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Set
import logging.handlers


class OSINTLogger:
    """Klasa zapewniająca strukturalne logowanie w formatach JSONL lub standardowym."""
    
    # Lista pól, które mogą zawierać dane wrażliwe
    SENSITIVE_FIELDS: Set[str] = {"username", "phone_number", "phone", "email", "password"}
    
    def __init__(
        self, 
        log_dir: Optional[Union[str, Path]] = None, 
        level: Union[str, int] = "INFO",
        app_name: str = "osint_super_kombajn",
        log_format: str = "json",
        max_log_files: int = 10,
        max_log_size_mb: int = 10
    ):
        """
        Inicjalizuje logger OSINT.

        Args:
            log_dir: Katalog dla logów. Jeśli None, używa './logs'.
            level: Poziom logowania jako string lub stała logging.
            app_name: Nazwa aplikacji używana w logach.
            log_format: Format logów - "json" lub "text".
            max_log_files: Maksymalna liczba plików logów w rotacji.
            max_log_size_mb: Maksymalny rozmiar pojedynczego pliku logu w MB.
        """
        self.log_dir = Path(log_dir or "./logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.app_name = app_name
        self.log_format = log_format.lower()
        
        # Konwersja poziomu logowania z tekstu na stałą
        if isinstance(level, str):
            level = getattr(logging, level.upper())
            
        # Przygotuj główny logger
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(level)
        self.logger.handlers.clear()  # Usuń istniejące handlery
        
        # Utwórz handlery
        self._add_console_handler(level)
        self._add_file_handler(level, max_log_files, max_log_size_mb)
        
        # Zapisz pierwszy log
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.info(
            "Logger zainicjalizowany", 
            log_dir=str(self.log_dir), 
            level=logging.getLevelName(level),
            format=self.log_format
        )
    
    def _add_console_handler(self, level: int) -> None:
        """Dodaje handler dla konsoli."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        if self.log_format == "json":
            console_formatter = logging.Formatter('%(message)s')
        else:
            console_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
            
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
    
    def _add_file_handler(self, level: int, max_files: int, max_size_mb: int) -> None:
        """Dodaje handler dla plików z rotacją."""
        timestamp = datetime.now().strftime("%Y%m%d")
        
        if self.log_format == "json":
            filename = f"{self.app_name}_{timestamp}.jsonl"
        else:
            filename = f"{self.app_name}_{timestamp}.log"
            
        log_path = self.log_dir / filename
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=max_files,
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        
        if self.log_format == "json":
            file_formatter = logging.Formatter('%(message)s')
        else:
            file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s] %(message)s')
            
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
    
    def _sanitize_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Maskuje dane wrażliwe w logach."""
        sanitized = data.copy()
        
        for key, value in sanitized.items():
            if key.lower() in self.SENSITIVE_FIELDS and isinstance(value, str):
                # Maskuj wszystko oprócz pierwszych 2 i ostatnich 2 znaków
                if len(value) > 6:
                    sanitized[key] = value[:2] + "*" * (len(value) - 4) + value[-2:]
                else:
                    sanitized[key] = "****"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_sensitive_data(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_sensitive_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
                
        return sanitized
    
    def _format_json_log(self, level: str, message: str, **kwargs) -> str:
        """Formatuje wpis logu jako JSON."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "application": self.app_name,
            "message": message,
            "process_id": os.getpid(),
            "thread_id": id(threading.current_thread()) if threading else 0
        }
        
        # Dodaj dodatkowe pola
        if kwargs:
            safe_kwargs = self._sanitize_sensitive_data(kwargs)
            log_entry.update(safe_kwargs)
            
        return json.dumps(log_entry, ensure_ascii=False)
    
    def info(self, message: str, **kwargs) -> None:
        """Loguje wiadomość na poziomie INFO."""
        if self.log_format == "json":
            self.logger.info(self._format_json_log("INFO", message, **kwargs))
        else:
            self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Loguje wiadomość na poziomie WARNING."""
        if self.log_format == "json":
            self.logger.warning(self._format_json_log("WARNING", message, **kwargs))
        else:
            self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Loguje wiadomość na poziomie ERROR."""
        if self.log_format == "json":
            log_data = kwargs.copy()
            if exc_info:
                import traceback
                log_data["exception"] = traceback.format_exc()
            self.logger.error(self._format_json_log("ERROR", message, **log_data))
        else:
            self.logger.error(message, exc_info=exc_info, extra=kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """Loguje wiadomość na poziomie DEBUG."""
        if self.log_format == "json":
            self.logger.debug(self._format_json_log("DEBUG", message, **kwargs))
        else:
            self.logger.debug(message, extra=kwargs)
    
    def critical(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Loguje wiadomość na poziomie CRITICAL."""
        if self.log_format == "json":
            log_data = kwargs.copy()
            if exc_info:
                import traceback
                log_data["exception"] = traceback.format_exc()
            self.logger.critical(self._format_json_log("CRITICAL", message, **log_data))
        else:
            self.logger.critical(message, exc_info=exc_info, extra=kwargs)
    
    def log_result(self, tool: str, result: Dict[str, Any]) -> None:
        """Loguje wynik działania narzędzia."""
        success = result.get("success", False)
        log_entry = {"tool": tool, "success": success}
        
        if success:
            self.info(f"Narzędzie {tool} zakończyło działanie pomyślnie", **log_entry)
        else:
            self.error(f"Narzędzie {tool} zgłosiło błąd: {result.get('error', 'Nieznany błąd')}", **log_entry)


# Dodanie wsparcia dla Python <3.10
import threading