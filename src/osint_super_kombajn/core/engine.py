"""
Silnik główny OSINT Super Kombajn.
"""
import asyncio
from typing import Dict, List, Any, Optional, Union

from osint_super_kombajn.config import config
from osint_super_kombajn.tools.sherlock.adapter import SherlockAdapter
from osint_super_kombajn.tools.phoneinfoga.adapter import PhoneInfogaAdapter
from osint_super_kombajn.tools.maigret.adapter import MaigretAdapter
from osint_super_kombajn.tools.exiftool.adapter import ExifToolAdapter
from osint_super_kombajn.tools.holehe.adapter import HoleheAdapter
from osint_super_kombajn.ai_agents.analyzers import AIAnalyzer

class OSINTEngine:
    """
    Główny silnik OSINT Super Kombajn.
    
    Koordynuje wykonanie narzędzi OSINT i analizę wyników.
    """
    
    def __init__(self):
        """Inicjalizuje silnik OSINT."""
        self.sherlock = SherlockAdapter()
        self.phoneinfoga = PhoneInfogaAdapter()
        self.maigret = MaigretAdapter()
        self.exiftool = ExifToolAdapter()
        self.holehe = HoleheAdapter()
        self.ai_analyzer = AIAnalyzer()
        
        self.results = {}
    
    async def analyze_username(self, username: str) -> Dict[str, Any]:
        """
        Analizuje nazwę użytkownika przy użyciu dostępnych narzędzi.
        
        Args:
            username: Nazwa użytkownika do analizy
            
        Returns:
            Wyniki analizy
        """
        # Zamiast używać asyncio.gather, wywołujemy każdą metodę osobno
        # aby uniknąć problemów z asynchronicznością w naszym mock'u
        sherlock_result = self.sherlock.search(username)
        maigret_result = self.maigret.search(username)
        
        return {
            "username": username,
            "sherlock": sherlock_result,
            "maigret": maigret_result
        }
    
    async def analyze_phone(self, phone: str) -> Dict[str, Any]:
        """
        Analizuje numer telefonu przy użyciu dostępnych narzędzi.
        
        Args:
            phone: Numer telefonu do analizy
            
        Returns:
            Wyniki analizy
        """
        result = self.phoneinfoga.search(phone)
        
        return {
            "phone": phone,
            "phoneinfoga": result
        }
    
    async def analyze_email(self, email: str) -> Dict[str, Any]:
        """
        Analizuje adres e-mail przy użyciu dostępnych narzędzi.
        
        Args:
            email: Adres e-mail do analizy
            
        Returns:
            Wyniki analizy
        """
        result = self.holehe.check_email(email)
        
        return {
            "email": email,
            "holehe": result
        }
    
    async def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analizuje plik przy użyciu dostępnych narzędzi.
        
        Args:
            file_path: Ścieżka do pliku do analizy
            
        Returns:
            Wyniki analizy
        """
        result = self.exiftool.extract_metadata(file_path)
        
        return {
            "file_path": file_path,
            "exiftool": result
        }
    
    async def run_ai_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Uruchamia analizę AI na zebranych danych.
        
        Args:
            data: Dane do analizy
            
        Returns:
            Wyniki analizy AI
        """
        if config["ai"]["enabled"]:
            return self.ai_analyzer.analyze(data)
        else:
            return {"message": "Analiza AI wyłączona w konfiguracji"}
