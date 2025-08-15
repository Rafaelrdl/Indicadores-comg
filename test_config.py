#!/usr/bin/env python3
"""
Script para testar se as configurações estão sendo carregadas corretamente
"""

import os
import sys

# Adicionar o diretório do app ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import Settings

def test_config():
    """Testa se as configurações estão carregando do .env"""
    settings = Settings()
    
    print("📝 CONFIGURAÇÕES CARREGADAS:")
    print(f"   ARKMEDS_EMAIL: {settings.arkmeds_email}")
    print(f"   ARKMEDS_PASSWORD: {'*' * len(settings.arkmeds_password) if settings.arkmeds_password else 'None'}")
    print(f"   ARKMEDS_BASE_URL: {settings.arkmeds_base_url}")
    print(f"   ARKMEDS_TOKEN: {'<token-presente>' if settings.arkmeds_token else 'None'}")
    
    if not settings.arkmeds_email or not settings.arkmeds_password:
        print("\n❌ PROBLEMA: Email ou senha não configurados!")
        return False
    
    print("\n✅ Configurações OK!")
    return True

if __name__ == "__main__":
    test_config()
