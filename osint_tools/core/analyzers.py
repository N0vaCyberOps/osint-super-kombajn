"""
Moduł zawierający analizatory wykorzystujące sztuczną inteligencję.
"""

import json
import os
import httpx
import hmac
import hashlib
import time
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential


class SecureAIClient:
    """Bezpieczny klient dla API sztucznej inteligencji."""
    
    def __init__(self, 
                api_key: Optional[str] = None, 
                base_url: Optional[str] = None,
                timeout: int = 60,
                max_retries: int = 3):
        """
        Inicjalizuje bezpiecznego klienta AI.
        
        Args:
            api_key: Klucz API. Jeśli None, używa zmiennej środowiskowej.
            base_url: Bazowy URL API. Jeśli None, używa domyślnego.
            timeout: Limit czasu w sekundach.
            max_retries: Maksymalna liczba ponownych prób.
        """
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("Wymagany klucz API. Ustaw zmienną środowiskową OPENROUTER_API_KEY.")
            
        self.base_url = base_url or os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.timeout = timeout
        self.max_retries = max_retries
    
    def _create_hmac_signature(self, payload: Dict[str, Any]) -> str:
        """
        Tworzy podpis HMAC dla ładunku.
        
        Args:
            payload: Ładunek do podpisania.
            
        Returns:
            Podpis HMAC.
        """
        # Użyj pierwszych 10 znaków klucza API jako wspólnego sekretu
        secret = self.api_key[:10].encode('utf-8')
        message = json.dumps(payload, sort_keys=True).encode('utf-8')
        signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
        return signature
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def query(self, 
                   prompt: str,
                   model: str = "anthropic/claude-3-opus-20240229", 
                   max_tokens: int = 2000,
                   temperature: float = 0.7,
                   system_message: str = "Jesteś ekspertem ds. analizy OSINT. Dostarcz dokładne, neutralne analizy."
                  ) -> Dict[str, Any]:
        """
        Wysyła zapytanie do API AI z zabezpieczeniami.
        
        Args:
            prompt: Tekst zapytania.
            model: Model AI do użycia.
            max_tokens: Maksymalna liczba tokenów w odpowiedzi.
            temperature: Temperatura generowania (losowość).
            system_message: Wiadomość systemowa dla modelu.
            
        Returns:
            Odpowiedź API.
        """
        # Przygotuj ładunek
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "request_id": f"osint_{int(time.time())}_{os.urandom(4).hex()}"
        }
        
        # Oblicz podpis
        signature = self._create_hmac_signature(payload)
        
        # Przygotuj nagłówki
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Request-Signature": signature,
            "User-Agent": "OSINTSuperKombajn/0.2.0"
        }
        
        try:
            # Wyślij zapytanie
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                # Waliduj odpowiedź
                result = response.json()
                if not self._validate_response(result):
                    raise ValueError("Nieprawidłowy format odpowiedzi API AI")
                    
                return self._process_response(result)
        except httpx.HTTPStatusError as e:
            return self._handle_http_error(e)
        except Exception as e:
            return {"success": False, "error": f"Zapytanie AI nie powiodło się: {str(e)}"}
    
    def _validate_response(self, response: Dict[str, Any]) -> bool:
        """
        Waliduje format odpowiedzi API.
        
        Args:
            response: Odpowiedź API.
            
        Returns:
            True jeśli format odpowiedzi jest prawidłowy, False w przeciwnym razie.
        """
        return (
            isinstance(response, dict) and
            "choices" in response and
            isinstance(response["choices"], list) and
            len(response["choices"]) > 0 and
            "message" in response["choices"][0] and
            "content" in response["choices"][0]["message"]
        )
    
    def _process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Przetwarza i strukturyzuje odpowiedź API.
        
        Args:
            response: Surowa odpowiedź API.
            
        Returns:
            Przetworzona odpowiedź.
        """
        try:
            text = response["choices"][0]["message"]["content"]
            return {
                "success": True,
                "text": text,
                "model": response.get("model", "unknown"),
                "usage": response.get("usage", {}),
                "sections": self._extract_sections(text)
            }
        except (KeyError, IndexError) as e:
            return {"success": False, "error": f"Nie udało się przetworzyć odpowiedzi AI: {str(e)}"}
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """
        Ekstrahuje strukturyzowane sekcje z odpowiedzi AI.
        
        Args:
            text: Tekst odpowiedzi.
            
        Returns:
            Słownik z sekcjami.
        """
        sections: Dict[str, str] = {"other": ""}
        current_section = "other"
        
        # Zdefiniuj markery sekcji
        section_markers = {
            "summary": ["podsumowanie", "summary", "overview"],
            "risks": ["zagrożenia", "ryzyka", "risks", "threats"],
            "recommendations": ["rekomendacje", "recommendations", "suggestions"]
        }
        
        # Przetwarzaj tekst linia po linii
        lines = text.split("\n")
        for line in lines:
            lower_line = line.lower()
            
            # Sprawdź, czy linia jest nagłówkiem sekcji
            new_section = None
            for section, markers in section_markers.items():
                if any(marker in lower_line for marker in markers):
                    new_section = section
                    if section not in sections:
                        sections[section] = ""
                    break
                    
            if new_section:
                current_section = new_section
            elif line.strip():
                sections[current_section] += line + "\n"
                
        # Wyczyść sekcje
        return {k: v.strip() for k, v in sections.items() if v.strip()}
    
    def _handle_http_error(self, error: httpx.HTTPStatusError) -> Dict[str, Any]:
        """
        Obsługuje błędy HTTP z API AI.
        
        Args:
            error: Błąd HTTP.
            
        Returns:
            Słownik z informacją o błędzie.
        """
        try:
            error_data = error.response.json()
            error_message = error_data.get("error", {}).get("message", str(error))
        except Exception:
            error_message = f"Błąd HTTP {error.response.status_code}"
            
        return {
            "success": False,
            "error": f"Błąd API AI: {error_message}",
            "status_code": error.response.status_code
        }


class TextAnalyzer:
    """Analizator tekstowy wykorzystujący modele AI."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Inicjalizuje analizator tekstowy.
        
        Args:
            api_key: Klucz API dla usługi AI. Jeśli None, używa zmiennej środowiskowej.
            base_url: Bazowy URL API. Jeśli None, używa domyślnego.
        """
        self.client = SecureAIClient(api_key=api_key, base_url=base_url)
        
    async def analyze(self, text_data: Union[str, Dict[str, Any], List[Dict[str, Any]]], model: str = "anthropic/claude-3-opus-20240229") -> Dict[str, Any]:
        """
        Analizuje dane tekstowe za pomocą modelu AI.

        Args:
            text_data: Tekst lub dane tekstowe do analizy.
            model: Model AI do użycia.

        Returns:
            Wyniki analizy.
        """
        prompt = f"""Proszę przeanalizuj poniższe dane OSINT i dostarcz:
1. Podsumowanie znalezionych informacji
2. Potencjalne zagrożenia lub ryzyka
3. Rekomendacje dotyczące dalszych kroków

Dane:
{json.dumps(text_data, indent=2, ensure_ascii=False) if isinstance(text_data, (dict, list)) else text_data}
"""

        return await self.client.query(
            prompt=prompt,
            model=model,
            system_message="Jesteś ekspertem ds. analizy OSINT. Dostarcz dokładne, neutralne analizy."
        )


class ProfileAnalyzer:
    """Analizator profili użytkowników wykorzystujący modele AI."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Inicjalizuje analizator profili.
        
        Args:
            api_key: Klucz API dla usługi AI. Jeśli None, używa zmiennej środowiskowej.
            base_url: Bazowy URL API. Jeśli None, używa domyślnego.
        """
        self.client = SecureAIClient(api_key=api_key, base_url=base_url)
        
    async def analyze(self, profile_data: Dict[str, Any], model: str = "anthropic/claude-3-opus-20240229") -> Dict[str, Any]:
        """
        Analizuje dane profilu użytkownika.

        Args:
            profile_data: Dane profilu do analizy.
            model: Model AI do użycia.

        Returns:
            Wyniki analizy behawioralnej.
        """
        prompt = f"""Przeprowadź analizę behawioralną profilu użytkownika:
1. Oceń charakter i zwyczaje użytkownika
2. Zidentyfikuj zainteresowania, hobby i wzorce aktywności
3. Wskaż potencjalnie narażone dane osobowe
4. Oceń poziom bezpieczeństwa cyfrowego

Dane:
{json.dumps(profile_data, indent=2, ensure_ascii=False)}
"""

        return await self.client.query(
            prompt=prompt,
            model=model,
            system_message="Jesteś specjalistą ds. analizy behawioralnej. Dostarcz etyczne analizy."
        )


async def analyze_results(results: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Analizuje wyniki narzędzi OSINT za pomocą AI.

    Args:
        results: Lista wyników z narzędzi OSINT.
        output_path: Ścieżka do zapisania wyników analizy AI.

    Returns:
        Wyniki analizy.
    """
    if not results:
        return {"success": False, "error": "Brak danych do analizy"}
        
    try:
        analyzer = TextAnalyzer()
        successful_results = [r for r in results if r.get("success", False)]
        
        if not successful_results:
            return {"success": False, "error": "Brak pomyślnych wyników do analizy"}
            
        analysis = await analyzer.analyze(successful_results)
        
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
                
        return analysis
    except Exception as e:
        return {"success": False, "error": f"Błąd analizy wyników: {str(e)}"}