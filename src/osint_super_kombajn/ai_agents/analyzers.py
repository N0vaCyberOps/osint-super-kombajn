# src/osint_super_kombajn/ai_agents/analyzers.py
"""
Moduł zawierający analizatory wykorzystujące sztuczną inteligencję.
"""

import json
import os
import httpx
from typing import Dict, List, Any, Optional, Union

class AIAnalyzer:
    """
    Klasa bazowa dla analizatorów wykorzystujących sztuczną inteligencję.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicjalizuje analizator AI.
        
        Args:
            api_key: Klucz API dla usługi AI. Jeśli None, próbuje pobrać z zmiennych środowiskowych.
        """
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("Brak klucza API dla usług AI. Ustaw zmienną środowiskową OPENROUTER_API_KEY lub przekaż klucz bezpośrednio.")
            
        self.base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    async def analyze(self, data: Dict[str, Any], model: str = "gpt-4") -> Dict[str, Any]:
        """
        Analizuje dane przy użyciu sztucznej inteligencji.
        
        Args:
            data: Dane do analizy
            model: Nazwa modelu do użycia (domyślnie "gpt-4")
            
        Returns:
            Wyniki analizy
        """
        raise NotImplementedError("Podklasy muszą implementować metodę analyze.")


class TextAnalyzer(AIAnalyzer):
    """
    Analizator tekstowy wykorzystujący modele AI.
    """
    
    async def analyze(self, text_data: Union[str, Dict[str, Any]], model: str = "anthropic/claude-3-opus-20240229") -> Dict[str, Any]:
        """
        Analizuje dane tekstowe przy użyciu modelu AI.
        
        Args:
            text_data: Tekst lub dane zawierające tekst do analizy
            model: Model AI do użycia
            
        Returns:
            Wyniki analizy
        """
        # Przygotuj tekst do analizy
        if isinstance(text_data, dict):
            # Serializuj słownik do JSON i dodaj wskazówki
            prompt = f"""Proszę przeanalizuj poniższe dane OSINT i dostarcz:
1. Podsumowanie znalezionych informacji
2. Potencjalne zagrożenia lub ryzyka związane z tymi danymi
3. Rekomendacje dotyczące dalszych kroków w badaniu

Dane:
{json.dumps(text_data, indent=2, ensure_ascii=False)}
"""
        else:
            prompt = f"""Proszę przeanalizuj poniższe dane OSINT i dostarcz:
1. Podsumowanie znalezionych informacji
2. Potencjalne zagrożenia lub ryzyka związane z tymi danymi
3. Rekomendacje dotyczące dalszych kroków w badaniu

Dane:
{text_data}
"""

        try:
            # Wykonaj zapytanie do API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "Jesteś ekspertem ds. analizy OSINT. Dostarczasz dokładne, neutralne i szczegółowe analizy danych wywiadowczych."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2000
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Wyciągnij tekst odpowiedzi
                if "choices" in result and len(result["choices"]) > 0:
                    analysis_text = result["choices"][0]["message"]["content"]
                    
                    # Ekstrahuj sekcje z tekstu
                    sections = self._parse_analysis_text(analysis_text)
                    
                    return {
                        "success": True,
                        "analysis": sections,
                        "raw_text": analysis_text,
                        "model": model
                    }
                else:
                    return {
                        "success": False,
                        "error": "Brak odpowiedzi od modelu AI",
                        "raw_response": result
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Błąd podczas analizy AI: {str(e)}"
            }
    
    def _parse_analysis_text(self, text: str) -> Dict[str, str]:
        """
        Parsuje tekst analizy na poszczególne sekcje.
        
        Args:
            text: Tekst analizy
            
        Returns:
            Słownik zawierający poszczególne sekcje
        """
        sections = {
            "summary": "",
            "risks": "",
            "recommendations": "",
            "other": ""
        }
        
        # Prosty parser sekcji
        current_section = "other"
        lines = text.split("\n")
        
        for line in lines:
            if "podsumowanie" in line.lower() or "summary" in line.lower() or "1." in line:
                current_section = "summary"
                continue
            elif "zagrożenia" in line.lower() or "ryzyka" in line.lower() or "risks" in line.lower() or "2." in line:
                current_section = "risks"
                continue
            elif "rekomendacje" in line.lower() or "recommendations" in line.lower() or "dalsze kroki" in line.lower() or "3." in line:
                current_section = "recommendations"
                continue
            
            # Dodaj linię do odpowiedniej sekcji
            if line.strip():
                sections[current_section] += line + "\n"
        
        # Usuń białe znaki na początku i końcu
        for key in sections:
            sections[key] = sections[key].strip()
            
        return sections


class ProfileAnalyzer(AIAnalyzer):
    """
    Analizator profili użytkowników wykorzystujący modele AI.
    """
    
    async def analyze(self, profile_data: Dict[str, Any], model: str = "anthropic/claude-3-opus-20240229") -> Dict[str, Any]:
        """
        Analizuje dane profilu użytkownika przy użyciu modelu AI.
        
        Args:
            profile_data: Dane profilu do analizy
            model: Model AI do użycia
            
        Returns:
            Wyniki analizy behawioralnej
        """
        # Przygotuj dane do analizy
        prompt = f"""Proszę przeprowadź analizę behawioralną profilu użytkownika na podstawie poniższych danych OSINT:

1. Oceń prawdopodobny charakter i zwyczaje użytkownika
2. Zidentyfikuj możliwe zainteresowania, hobby i wzorce aktywności
3. Podaj wskazówki dotyczące potencjalnych danych osobowych, które mogą być narażone
4. Oceń poziom bezpieczeństwa cyfrowego użytkownika

Dane:
{json.dumps(profile_data, indent=2, ensure_ascii=False)}
"""

        try:
            # Wykonaj zapytanie do API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "Jesteś specjalistą ds. analizy behawioralnej i bezpieczeństwa cyfrowego. Dostarczasz etyczne, faktyczne i neutralne analizy wzorców użytkowników."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2000
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Wyciągnij tekst odpowiedzi
                if "choices" in result and len(result["choices"]) > 0:
                    analysis_text = result["choices"][0]["message"]["content"]
                    
                    # Ekstrahuj sekcje z tekstu
                    sections = self._parse_behavioral_analysis(analysis_text)
                    
                    return {
                        "success": True,
                        "analysis": sections,
                        "raw_text": analysis_text,
                        "model": model
                    }
                else:
                    return {
                        "success": False,
                        "error": "Brak odpowiedzi od modelu AI",
                        "raw_response": result
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Błąd podczas analizy behawioralnej: {str(e)}"
            }
    
    def _parse_behavioral_analysis(self, text: str) -> Dict[str, str]:
        """
        Parsuje tekst analizy behawioralnej na poszczególne sekcje.
        
        Args:
            text: Tekst analizy
            
        Returns:
            Słownik zawierający poszczególne sekcje
        """
        sections = {
            "character": "",
            "interests": "",
            "personal_data": "",
            "security_level": "",
            "other": ""
        }
        
        # Prosty parser sekcji
        current_section = "other"
        lines = text.split("\n")
        
        for line in lines:
            if "charakter" in line.lower() or "zwyczaje" in line.lower() or "1." in line:
                current_section = "character"
                continue
            elif "zainteresowania" in line.lower() or "hobby" in line.lower() or "wzorce" in line.lower() or "2." in line:
                current_section = "interests"
                continue
            elif "dane osobowe" in line.lower() or "prywatne" in line.lower() or "3." in line:
                current_section = "personal_data"
                continue
            elif "bezpieczeństwo" in line.lower() or "security" in line.lower() or "4." in line:
                current_section = "security_level"
                continue
            
            # Dodaj linię do odpowiedniej sekcji
            if line.strip():
                sections[current_section] += line + "\n"
        
        # Usuń białe znaki na początku i końcu
        for key in sections:
            sections[key] = sections[key].strip()
            
        return sections
