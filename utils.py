import re
from typing import Optional

def normalize_address(address: str, is_alias: bool = False) -> str:
    """
    Normaliza direcciones de Ethereum a minúsculas y alias eliminando el '@'.
    Asegura consistencia entre el Agente AI, la DB y Circle.
    """
    if not isinstance(address, str):
        return ""
    
    if is_alias:
        return address.strip().lower().lstrip('@')
    
    return address.strip().lower()

def is_valid_alias(alias: str) -> bool:
    """Valida el patrón de alias definido en la arquitectura."""
    pattern = r'^@[a-zA-Z0-9_]{3,20}$'
    return bool(re.match(pattern, alias))
