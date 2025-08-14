#!/usr/bin/env python3
"""Script para verificar as configurações."""

from app.core.config import get_settings

def main():
    print("=== CONFIGURAÇÕES ===")
    
    settings = get_settings()
    
    print(f"Email: {'✅ Configurado' if settings.arkmeds_email else '❌ Não configurado'}")
    print(f"Email value: {settings.arkmeds_email}")
    print(f"Password: {'✅ Configurado' if settings.arkmeds_password else '❌ Não configurado'}")
    print(f"Password value: {'***' if settings.arkmeds_password else 'None'}")
    print(f"Token: {'✅ Configurado' if settings.arkmeds_token else '❌ Não configurado'}")
    print(f"Token value: {'***' if settings.arkmeds_token else 'None'}")
    print(f"Base URL: {settings.arkmeds_base_url}")

if __name__ == "__main__":
    main()
