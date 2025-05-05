"""
Moduł konfiguracyjny OSINT Super Kombajn.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

import yaml

# Domyślne ścieżki
BASE_DIR = Path(__file__).parent.parent.parent.parent
CONFIG_DIR = BASE_DIR / "configs"
DEFAULT_CONFIG_FILE = CONFIG_DIR / "settings.yaml"

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Ładuje konfigurację z pliku YAML.
    
    Args:
        config_path: Ścieżka do pliku konfiguracyjnego. Jeśli None, używa domyślnej.
        
    Returns:
        Słownik z konfiguracją
    """
    config_path = config_path or DEFAULT_CONFIG_FILE
    
    # Domyślna konfiguracja
    default_config = {
        "tools": {
            "sherlock": {
                "path": os.getenv("SHERLOCK_PATH", "./tools/sherlock"),
                "timeout": int(os.getenv("SHERLOCK_TIMEOUT", "300"))
            },
            "phoneinfoga": {
                "path": os.getenv("PHONEINFOGA_PATH", "./tools/phoneinfoga"),
                "timeout": int(os.getenv("PHONEINFOGA_TIMEOUT", "120"))
            },
            "maigret": {
                "path": os.getenv("MAIGRET_PATH", "./tools/maigret"),
                "timeout": int(os.getenv("MAIGRET_TIMEOUT", "300"))
            },
            "exiftool": {
                "path": os.getenv("EXIFTOOL_PATH", "./tools/exiftool"),
                "timeout": int(os.getenv("EXIFTOOL_TIMEOUT", "60"))
            },
            "holehe": {
                "path": os.getenv("HOLEHE_PATH", "./tools/holehe"),
                "timeout": int(os.getenv("HOLEHE_TIMEOUT", "180"))
            }
        },
        "output": {
            "results_dir": os.getenv("RESULTS_DIR", "./results"),
            "log_dir": os.getenv("LOG_DIR", "./logs"),
            "log_level": os.getenv("LOG_LEVEL", "INFO")
        },
        "ai": {
            "enabled": os.getenv("ENABLE_AI_ANALYSIS", "True").lower() in ("true", "1", "yes"),
            "api_key": os.getenv("OPENROUTER_API_KEY", ""),
            "base_url": os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            "default_model": "anthropic/claude-3-opus-20240229"
        },
        "app": {
            "debug": os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
        }
    }
    
    # Jeśli plik konfiguracyjny istnieje, nadpisz domyślne wartości
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                file_config = yaml.safe_load(f)
                
            # Rekurencyjne nadpisywanie domyślnej konfiguracji
            merge_configs(default_config, file_config)
        except Exception as e:
            print(f"Błąd podczas ładowania konfiguracji: {e}")
    
    return default_config

def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> None:
    """
    Rekurencyjnie nadpisuje wartości w konfiguracji bazowej.
    
    Args:
        base_config: Konfiguracja bazowa do nadpisania
        override_config: Konfiguracja nadpisująca
    """
    for key, value in override_config.items():
        if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
            merge_configs(base_config[key], value)
        else:
            base_config[key] = value

# Załaduj konfigurację przy imporcie modułu
config = load_config()
