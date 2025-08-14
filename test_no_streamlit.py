#!/usr/bin/env python3
"""Script para testar sem Streamlit."""

import sys

# Simular que streamlit não está disponível
if 'streamlit' in sys.modules:
    del sys.modules['streamlit']

from app.core.config import Settings

def main():
    print("=== TESTANDO SEM STREAMLIT ===")
    
    # Teste with from_streamlit_secrets (deve fazer fallback)
    settings = Settings.from_streamlit_secrets()
    print(f"Email: {settings.arkmeds_email}")
    print(f"Password: {'***' if settings.arkmeds_password else 'None'}")
    print(f"Base URL: {settings.arkmeds_base_url}")

if __name__ == "__main__":
    main()
