#!/usr/bin/env python3
"""Script para testar nossa classe Settings atual."""

from app.core.config import Settings

def main():
    print("=== TESTANDO SETTINGS ATUAL ===")
    
    # Teste direto
    settings = Settings()
    print(f"Email (direto): {settings.arkmeds_email}")
    print(f"Password (direto): {'***' if settings.arkmeds_password else 'None'}")
    print(f"Base URL (direto): {settings.arkmeds_base_url}")
    
    # Teste with from_streamlit_secrets
    settings2 = Settings.from_streamlit_secrets()
    print(f"Email (secrets): {settings2.arkmeds_email}")
    print(f"Password (secrets): {'***' if settings2.arkmeds_password else 'None'}")
    print(f"Base URL (secrets): {settings2.arkmeds_base_url}")

if __name__ == "__main__":
    main()
