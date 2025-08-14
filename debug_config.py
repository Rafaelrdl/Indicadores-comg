#!/usr/bin/env python3
"""Script para debugar step by step."""

import sys
import os
from pathlib import Path

# Simular que streamlit não está disponível
if 'streamlit' in sys.modules:
    del sys.modules['streamlit']

print("1. Verificando .env:")
env_file = Path(".env")
print(f"   Existe: {env_file.exists()}")

print("\n2. Carregando dotenv manualmente:")
from dotenv import load_dotenv
loaded = load_dotenv()
print(f"   Loaded: {loaded}")
print(f"   EMAIL: {os.getenv('ARKMEDS_EMAIL', 'NÃO ENCONTRADA')}")

print("\n3. Testando Pydantic direto:")
from pydantic import Field
from pydantic_settings import BaseSettings

class TestSettings(BaseSettings):
    model_config = {
        "extra": "ignore",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "env_prefix": "",
    }
    
    arkmeds_email: str | None = Field(default=None)
    arkmeds_password: str | None = Field(default=None)
    arkmeds_base_url: str = Field(default="https://api.exemplo.com")
    arkmeds_token: str | None = Field(default=None)

test_settings = TestSettings()
print(f"   Email: {test_settings.arkmeds_email}")
print(f"   Base URL: {test_settings.arkmeds_base_url}")

print("\n4. Testando nossa Settings:")
from app.core.config import Settings

# Reset global settings
import app.core.config
app.core.config._settings = None

our_settings = Settings()
print(f"   Email: {our_settings.arkmeds_email}")
print(f"   Base URL: {our_settings.arkmeds_base_url}")

print("\n5. Testando from_streamlit_secrets:")
fallback_settings = Settings.from_streamlit_secrets()
print(f"   Email: {fallback_settings.arkmeds_email}")
print(f"   Base URL: {fallback_settings.arkmeds_base_url}")

if __name__ == "__main__":
    pass
