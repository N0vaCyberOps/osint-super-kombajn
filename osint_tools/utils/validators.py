"""
Moduł zawierający funkcje walidacyjne dla danych wejściowych OSINT Super Kombajn.
"""

import re
import os
import shlex
from pathlib import Path
from typing import Union, Literal, Any, Optional
import ipaddress

# Standardowa biblioteka dla walidacji numerów telefonów (wymaga instalacji)
try:
    import phonenumbers
    from phonenumbers import NumberParseException
    PHONENUMBERS_AVAILABLE = True
except ImportError:
    PHONENUMBERS_AVAILABLE = False

ValidationResult = Union[bool, str]
ValidationType = Literal["username", "email", "phone", "file", "domain", "ip", "url", "none"]


def validate_input(input_type: ValidationType, input_value: Any) -> ValidationResult:
    """
    Waliduje dane wejściowe według typu.

    Args:
        input_type: Typ danych wejściowych do walidacji.
        input_value: Wartość do walidacji.

    Returns:
        True jeśli dane są poprawne, inaczej komunikat błędu.
    """
    if input_value is None:
        return "Wartość nie może być pusta"
        
    validators = {
        "username": validate_username,
        "email": validate_email,
        "phone": validate_phone,
        "file": validate_file,
        "domain": validate_domain,
        "ip": validate_ip,
        "url": validate_url,
        "none": lambda x: True
    }
    
    validator = validators.get(input_type)
    if validator:
        return validator(input_value)
    return f"Nieznany typ walidacji: {input_type}"


def validate_username(username: str) -> ValidationResult:
    """
    Waliduje nazwę użytkownika.
    
    Args:
        username: Nazwa użytkownika do sprawdzenia.
        
    Returns:
        True jeśli nazwa jest poprawna, inaczej komunikat błędu.
    """
    if not isinstance(username, str):
        return "Nazwa użytkownika musi być ciągiem znaków"
        
    if len(username) < 2 or len(username) > 64:
        return "Nazwa użytkownika musi mieć od 2 do 64 znaków"
        
    # Dopuszczamy tylko alfanumeryczne znaki, podkreślenia, kropki i myślniki
    if not re.match(r'^[a-zA-Z0-9._-]+$', username):
        return "Nazwa użytkownika zawiera niedozwolone znaki (dozwolone: litery, cyfry, ., _ i -)"
        
    # Sprawdź, czy nie zawiera potencjalnie niebezpiecznych znaków dla poleceń systemowych
    if any(c in username for c in ';|&<>$"`\\\''):
        return "Nazwa użytkownika zawiera potencjalnie niebezpieczne znaki"
        
    return True


def validate_email(email: str) -> ValidationResult:
    """
    Waliduje adres e-mail.
    
    Args:
        email: Adres e-mail do sprawdzenia.
        
    Returns:
        True jeśli adres jest poprawny, inaczej komunikat błędu.
    """
    if not isinstance(email, str):
        return "E-mail musi być ciągiem znaków"
        
    if len(email) > 254:
        return "Adres e-mail jest zbyt długi (maksymalnie 254 znaki)"
        
    # Zgodny z RFC 5322
    email_regex = r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    if not re.match(email_regex, email):
        return "Nieprawidłowy format adresu e-mail"
        
    # Sprawdź, czy domena ma prawidłowy format
    parts = email.split('@')
    if len(parts) != 2:
        return "Adres e-mail musi zawierać dokładnie jeden znak @"
        
    if not re.match(r'^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$', parts[1]):
        return "Nieprawidłowa domena w adresie e-mail"
        
    # Sprawdź, czy domena zawiera co najmniej jedną kropkę i TLD ma co najmniej 2 znaki
    domain_parts = parts[1].split('.')
    if len(domain_parts) < 2 or len(domain_parts[-1]) < 2:
        return "Domena musi zawierać co najmniej jedną kropkę i TLD co najmniej 2 znaki"
        
    # Sprawdź, czy nie zawiera potencjalnie niebezpiecznych znaków dla poleceń systemowych
    if any(c in email for c in ';|&<>$"`\\'):
        return "Adres e-mail zawiera potencjalnie niebezpieczne znaki"
        
    return True


def validate_phone(phone: str) -> ValidationResult:
    """
    Waliduje numer telefonu.
    
    Args:
        phone: Numer telefonu do sprawdzenia.
        
    Returns:
        True jeśli numer jest poprawny, inaczej komunikat błędu.
    """
    if not isinstance(phone, str):
        return "Numer telefonu musi być ciągiem znaków"
        
    # Użyj biblioteki phonenumbers jeśli dostępna
    if PHONENUMBERS_AVAILABLE:
        try:
            parsed_number = phonenumbers.parse(phone, None)
            if not phonenumbers.is_valid_number(parsed_number):
                return "Nieprawidłowy numer telefonu"
            return True
        except NumberParseException:
            return "Nie można sparsować numeru telefonu"
    
    # Prosta walidacja, jeśli biblioteka nie jest dostępna
    # Usuń wszystkie nieistotne znaki
    cleaned = re.sub(r'[\s()-]', '', phone)
    
    # Sprawdź, czy zaczyna się od + i ma co najmniej 7 cyfr
    if not re.match(r'^\+?[0-9]{7,15}$', cleaned):
        return "Numer telefonu musi zawierać + (opcjonalnie) i od 7 do 15 cyfr"
        
    # Sprawdź, czy nie zawiera potencjalnie niebezpiecznych znaków dla poleceń systemowych
    if any(c in phone for c in ';|&<>$"`\\'):
        return "Numer telefonu zawiera potencjalnie niebezpieczne znaki"
        
    return True


def validate_file(file_path: Union[str, Path]) -> ValidationResult:
    """
    Waliduje ścieżkę do pliku.
    
    Args:
        file_path: Ścieżka do pliku do sprawdzenia.
        
    Returns:
        True jeśli plik istnieje i jest dostępny, inaczej komunikat błędu.
    """
    try:
        file_path = Path(file_path) if isinstance(file_path, str) else file_path
        
        if not file_path.exists():
            return f"Plik nie istnieje: {file_path}"
            
        if not file_path.is_file():
            return f"Ścieżka nie wskazuje na plik: {file_path}"
            
        if not os.access(file_path, os.R_OK):
            return f"Brak uprawnień do odczytu pliku: {file_path}"
            
        # Sprawdź maksymalny rozmiar pliku (np. 100 MB)
        max_size_mb = 100
        if file_path.stat().st_size > max_size_mb * 1024 * 1024:
            return f"Plik jest zbyt duży (ponad {max_size_mb} MB)"
            
        return True
    except Exception as e:
        return f"Błąd sprawdzania pliku: {str(e)}"


def validate_domain(domain: str) -> ValidationResult:
    """
    Waliduje nazwę domeny.
    
    Args:
        domain: Nazwa domeny do sprawdzenia.
        
    Returns:
        True jeśli domena ma prawidłowy format, inaczej komunikat błędu.
    """
    if not isinstance(domain, str):
        return "Domena musi być ciągiem znaków"
        
    # Usuń protokół, jeśli istnieje
    if domain.startswith(('http://', 'https://')):
        parts = domain.split('://', 1)
        domain = parts[1]
        
    # Usuń ścieżkę, jeśli istnieje
    domain = domain.split('/', 1)[0]
    
    # Usuń port, jeśli istnieje
    domain = domain.split(':', 1)[0]
    
    # Sprawdź poprawność formatu domeny
    domain_regex = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    if not re.match(domain_regex, domain):
        return "Nieprawidłowy format domeny"
        
    # Sprawdź, czy TLD ma co najmniej 2 znaki
    if len(domain.split('.')[-1]) < 2:
        return "TLD domeny musi mieć co najmniej 2 znaki"
        
    # Sprawdź, czy nie zawiera potencjalnie niebezpiecznych znaków dla poleceń systemowych
    if any(c in domain for c in ';|&<>$"`\\'):
        return "Domena zawiera potencjalnie niebezpieczne znaki"
        
    return True


def validate_ip(ip: str) -> ValidationResult:
    """
    Waliduje adres IP (IPv4 lub IPv6).
    
    Args:
        ip: Adres IP do sprawdzenia.
        
    Returns:
        True jeśli adres IP ma prawidłowy format, inaczej komunikat błędu.
    """
    if not isinstance(ip, str):
        return "Adres IP musi być ciągiem znaków"
        
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return "Nieprawidłowy format adresu IP"


def validate_url(url: str) -> ValidationResult:
    """
    Waliduje URL.
    
    Args:
        url: URL do sprawdzenia.
        
    Returns:
        True jeśli URL ma prawidłowy format, inaczej komunikat błędu.
    """
    if not isinstance(url, str):
        return "URL musi być ciągiem znaków"
        
    # Sprawdź, czy URL zaczyna się od http:// lub https://
    if not url.startswith(('http://', 'https://')):
        return "URL musi zaczynać się od http:// lub https://"
        
    # Regex dla podstawowej walidacji URL
    url_regex = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
    if not re.match(url_regex, url):
        return "Nieprawidłowy format URL"
        
    # Sprawdź, czy nie zawiera potencjalnie niebezpiecznych znaków dla poleceń systemowych
    if any(c in url for c in ';|&<>$"`\\'):
        return "URL zawiera potencjalnie niebezpieczne znaki"
        
    return True


def sanitize_command_input(input_str: str) -> str:
    """
    Sanityzuje dane wejściowe dla poleceń systemowych.
    
    Args:
        input_str: Ciąg znaków do sanityzacji.
        
    Returns:
        Sanityzowany ciąg znaków.
    """
    # Usuń znaki sterujące i metaznaki powłoki
    sanitized = re.sub(r'[;&|()<>$`\\"\']', '', input_str)
    return sanitized


def safe_command_args(command: list) -> list:
    """
    Konwertuje argumenty polecenia na bezpieczny format.
    
    Args:
        command: Lista argumentów polecenia.
        
    Returns:
        Lista bezpiecznych argumentów polecenia.
    """
    return [shlex.quote(arg) for arg in command]