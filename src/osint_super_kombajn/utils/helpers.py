"""
Moduł pomocniczy z funkcjami użytkowymi dla OSINT Super Kombajn.
"""
import os
import json
import yaml
import datetime
from pathlib import Path
from typing import Dict, List, Any, Union, Optional

def ensure_dir(directory: Union[str, Path]) -> Path:
    """
    Upewnia się, że katalog istnieje, tworząc go w razie potrzeby.
    
    Args:
        directory: Ścieżka do katalogu
        
    Returns:
        Obiekt Path dla katalogu
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory

def save_json(data: Dict[str, Any], file_path: Union[str, Path]) -> Path:
    """
    Zapisuje dane w formacie JSON.
    
    Args:
        data: Dane do zapisania
        file_path: Ścieżka do pliku
        
    Returns:
        Obiekt Path dla zapisanego pliku
    """
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return file_path

def load_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Wczytuje dane z pliku JSON.
    
    Args:
        file_path: Ścieżka do pliku
        
    Returns:
        Wczytane dane
    """
    file_path = Path(file_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_yaml(data: Dict[str, Any], file_path: Union[str, Path]) -> Path:
    """
    Zapisuje dane w formacie YAML.
    
    Args:
        data: Dane do zapisania
        file_path: Ścieżka do pliku
        
    Returns:
        Obiekt Path dla zapisanego pliku
    """
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    
    return file_path

def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Wczytuje dane z pliku YAML.
    
    Args:
        file_path: Ścieżka do pliku
        
    Returns:
        Wczytane dane
    """
    file_path = Path(file_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def generate_timestamp() -> str:
    """
    Generuje znacznik czasu w formacie YYYYMMDD_HHMMSS.
    
    Returns:
        Znacznik czasu jako string
    """
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def generate_output_filename(prefix: str, extension: str = "json") -> str:
    """
    Generuje nazwę pliku wyjściowego z prefiksem i znacznikiem czasu.
    
    Args:
        prefix: Prefiks nazwy pliku
        extension: Rozszerzenie pliku (bez kropki)
        
    Returns:
        Nazwa pliku
    """
    timestamp = generate_timestamp()
    return f"{prefix}_{timestamp}.{extension}"
