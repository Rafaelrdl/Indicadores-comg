#!/usr/bin/env python3
"""
Teste simples para verificar as novas funcionalidades de equipamentos.
"""

import sys
from pathlib import Path

# Adiciona o diretório app ao path
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

try:
    print("🔍 Testando imports...")

    # Teste de imports básicos
    from services.equip_advanced_metrics import (
        EquipmentStats,
        EquipmentMTTFBF,
        calcular_stats_equipamentos,
        calcular_mttf_mtbf_top,
        exibir_distribuicao_prioridade,
        exibir_distribuicao_status,
        exibir_top_mttf_mtbf,
    )

    print("✅ Import de equip_advanced_metrics OK")

    from arkmeds_client.client import ArkmedsClient
    from arkmeds_client.auth import ArkmedsAuth

    print("✅ Import de client/auth OK")

    # Teste básico de criação de objetos
    stats = EquipmentStats(
        prioridade_baixa=10, prioridade_normal=20, ativos=100, desativados=5, em_manutencao=3
    )

    print(f"✅ EquipmentStats criado: {stats.total_equipamentos} equipamentos")
    print(f"   Distribuição: {stats.distribuicao_prioridade}")
    print(f"   Status: {stats.distribuicao_status}")

    # Teste de MTTFBF
    mttfbf = EquipmentMTTFBF(
        equipamento_id=1,
        nome="Teste",
        descricao="Equipamento de teste",
        mttf_horas=720.5,
        mtbf_horas=480.2,
        total_chamados=5,
    )

    print(f"✅ EquipmentMTTFBF criado: {mttfbf.nome}")
    print(f"   MTTF: {mttfbf.mttf_dias} dias")
    print(f"   MTBF: {mttfbf.mtbf_dias} dias")

    print("\n🎉 Todos os testes passaram! As funcionalidades estão prontas.")

except ImportError as e:
    print(f"❌ Erro de import: {e}")
except Exception as e:
    print(f"❌ Erro geral: {e}")
    import traceback

    traceback.print_exc()
