"""
Moduł zawierający narzędzia konfiguracji dla OSINT Super Kombajn.
"""

import os
import yaml
from typing import Dict, Any, Optional, TypeVar, List, cast
from pathlib import Path

T = TypeVar('T')


class ConfigManager:
    """Menedżer konfiguracji aplikacji."""
    
    def __init__(self, config_file: Optional[Path] = None, env_prefix: str = "OSINT_"):
        """
        Inicjalizuje menedżera konfiguracji.
        
        Args:
            config_file: Ścieżka do pliku konfiguracyjnego.
            env_prefix: Prefiks dla zmiennych środowiskowych.
        """
        self.config_file = config_file or Path("./configs/settings.yaml")
        self.env_prefix = env_prefix
        self._config: Dict[str, Any] = {}
        self._loaded = False
    
    def load(self) -> Dict[str, Any]:
        """
        Ładuje konfigurację z pliku i zmiennych środowiskowych.
        
        Returns:
            Słownik z konfiguracją.
        """
        default_config = self._get_default_config()
        file_config = self._load_from_file()
        env_config = self._load_from_env()
        
        # Łączenie konfiguracji z priorytetem: env > file > default
        self._config = self._deep_merge(default_config, file_config)
        self._config = self._deep_merge(self._config, env_config)
        self._loaded = True
        
        return self._config
    
    def get(self, key: str, default: Optional[T] = None) -> T:
        """
        Pobiera wartość konfiguracji po kluczu.
        
        Args:
            key: Klucz konfiguracji (może zawierać kropki dla zagnieżdżonych wartości).
            default: Domyślna wartość, jeśli klucz nie istnieje.
            
        Returns:
            Wartość konfiguracji lub domyślna wartość.
        """
        if not self._loaded:
            self.load()
            
        # Obsługa zagnieżdżonych kluczy z notacją kropkową
        parts = key.split('.')
        config = self._config
        
        for part in parts[:-1]:
            if part not in config or not isinstance(config[part], dict):
                return cast(T, default)
            config = config[part]
            
        return cast(T, config.get(parts[-1], default))
    
    def get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        """
        Pobiera konfigurację dla określonego narzędzia.
        
        Args:
            tool_name: Nazwa narzędzia.
            
        Returns:
            Słownik z konfiguracją narzędzia.
        """
        return cast(Dict[str, Any], self.get(f"tools.{tool_name}", {}))
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Zwraca pełną konfigurację jako słownik.
        
        Returns:
            Słownik z pełną konfiguracją.
        """
        if not self._loaded:
            self.load()
        return self._config.copy()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Zwraca domyślną konfigurację.
        
        Returns:
            Słownik z domyślną konfiguracją.
        """
        return {
            "version": "0.2.0",
            "logging": {
                "level": "INFO",
                "format": "json",
                "max_files": 10,
                "max_size_mb": 10
            },
            "tools": {
                "sherlock": {"timeout": 300, "max_retries": 3},
                "phoneinfoga": {"timeout": 300, "max_retries": 3},
                "maigret": {"timeout": 300, "max_retries": 3},
                "exiftool": {"timeout": 300, "max_retries": 3},
                "holehe": {"timeout": 300, "max_retries": 3}
            },
            "api": {
                "ai": {
                    "enabled": False,
                    "provider": "openrouter",
                    "model": "anthropic/claude-3-opus-20240229",
                    "rate_limit": 5,
                    "retry_attempts": 3
                }
            },
            "performance": {
                "max_workers": 5,
                "cache_ttl": 3600,
                "parallel_tools": True
            },
            "security": {
                "sanitize_inputs": True,
                "rate_limiting": True,
                "mask_sensitive_data": True
            },
            "report": {
                "default_format": "html",
                "include_metadata": True,
                "include_ai_analysis": True
            }
        }
    
    def _load_from_file(self) -> Dict[str, Any]:
        """
        Ładuje konfigurację z pliku YAML.
        
        Returns:
            Słownik z konfiguracją z pliku.
        """
        if not self.config_file.exists():
            return {}
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Błąd ładowania konfiguracji z {self.config_file}: {e}")
            return {}
    
    def _load_from_env(self) -> Dict[str, Any]:
        """
        Ładuje konfigurację ze zmiennych środowiskowych.
        
        Returns:
            Słownik z konfiguracją ze zmiennych środowiskowych.
        """
        config: Dict[str, Any] = {}
        
        # Pobierz wszystkie zmienne środowiskowe z określonym prefiksem
        for key, value in os.environ.items():
            if key.startswith(self.env_prefix):
                # Usuń prefiks i konwertuj na małe litery
                config_key = key[len(self.env_prefix):].lower()
                
                # Zastąp podwójne podkreślenie kropką dla zagnieżdżonych kluczy
                if "__" in config_key:
                    parts = config_key.split("__")
                    self._set_nested_dict(config, parts, value)
                else:
                    config[config_key] = self._parse_env_value(value)
        
        return config
    
    def _set_nested_dict(self, config: Dict[str, Any], keys: List[str], value: str) -> None:
        """
        Ustawia wartość w zagnieżdżonym słowniku.
        
        Args:
            config: Słownik do ustawienia wartości.
            keys: Lista kluczy (ścieżka do wartości).
            value: Wartość do ustawienia.
        """
        current = config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            if not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        current[keys[-1]] = self._parse_env_value(value)
    
    def _parse_env_value(self, value: str) -> Any:
        """
        Parsuje wartość ze zmiennej środowiskowej na odpowiedni typ.
        
        Args:
            value: Wartość ze zmiennej środowiskowej.
            
        Returns:
            Sparsowana wartość.
        """
        # Konwersja "true"/"false" na wartość logiczną
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False
            
        # Konwersja na liczbę całkowitą, jeśli możliwe
        try:
            return int(value)
        except ValueError:
            pass
            
        # Konwersja na liczbę zmiennoprzecinkową, jeśli możliwe
        try:
            return float(value)
        except ValueError:
            pass
            
        # Zwróć jako ciąg znaków
        return value
    
    def _deep_merge(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Głębokie łączenie dwóch słowników.
        
        Args:
            dict1: Pierwszy słownik.
            dict2: Drugi słownik (zastępuje wartości z pierwszego słownika).
            
        Returns:
            Połączony słownik.
        """
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result