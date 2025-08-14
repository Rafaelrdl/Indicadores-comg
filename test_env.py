#!/usr/bin/env python3
"""Script para testar carregamento de .env."""

import os
from pathlib import Path

# Verificar se arquivo .env existe
env_file = Path(".env")
print(f"Arquivo .env existe: {env_file.exists()}")
print(f"Caminho completo: {env_file.absolute()}")

if env_file.exists():
    print(f"Tamanho do arquivo: {env_file.stat().st_size} bytes")
    print("\nConteúdo do .env:")
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
        print(content[:200] + "..." if len(content) > 200 else content)

# Testar variáveis de ambiente diretamente
print(f"\n=== VARIÁVEIS DE AMBIENTE ===")
print(f"ARKMEDS_EMAIL: {os.getenv('ARKMEDS_EMAIL', 'NÃO ENCONTRADA')}")
print(f"ARKMEDS_PASSWORD: {os.getenv('ARKMEDS_PASSWORD', 'NÃO ENCONTRADA')}")
print(f"ARKMEDS_BASE_URL: {os.getenv('ARKMEDS_BASE_URL', 'NÃO ENCONTRADA')}")

# Testar com python-dotenv
try:
    from dotenv import load_dotenv
    print(f"\n=== TESTANDO COM DOTENV ===")
    loaded = load_dotenv()
    print(f"Dotenv carregado: {loaded}")
    print(f"ARKMEDS_EMAIL após dotenv: {os.getenv('ARKMEDS_EMAIL', 'NÃO ENCONTRADA')}")
    print(f"ARKMEDS_PASSWORD após dotenv: {os.getenv('ARKMEDS_PASSWORD', 'NÃO ENCONTRADA')}")
    print(f"ARKMEDS_BASE_URL após dotenv: {os.getenv('ARKMEDS_BASE_URL', 'NÃO ENCONTRADA')}")
except ImportError:
    print("python-dotenv não instalado")

# Testar Pydantic diretamente
try:
    from pydantic import Field
    from pydantic_settings import BaseSettings
    
    print(f"\n=== TESTANDO PYDANTIC SETTINGS ===")
    
    class TestSettings(BaseSettings):
        model_config = {
            "extra": "ignore",  # Allow extra fields to be ignored
            "env_file": ".env",
            "env_file_encoding": "utf-8", 
            "case_sensitive": False,
            "env_prefix": "",
        }
        
        arkmeds_email: str | None = Field(default=None)
        arkmeds_password: str | None = Field(default=None)
        arkmeds_base_url: str = Field(default="https://api.exemplo.com")
        arkmeds_token: str | None = Field(default=None)
    
    settings = TestSettings()
    print(f"Email: {settings.arkmeds_email}")
    print(f"Password: {'***' if settings.arkmeds_password else 'None'}")
    print(f"Base URL: {settings.arkmeds_base_url}")
    print(f"Token: {'***' if settings.arkmeds_token else 'None'}")
    
except Exception as e:
    print(f"Erro no Pydantic: {e}")

if __name__ == "__main__":
    pass
