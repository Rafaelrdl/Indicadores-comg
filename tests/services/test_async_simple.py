"""Script simples para testar funções async dos serviços."""

import asyncio
import sys
import os

# Adicionar o path do projeto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


async def test_services():
    """Testa as funções async dos serviços."""

    print("🧪 TESTANDO SERVIÇOS ASYNC")
    print("=" * 40)

    try:
        # Teste 1: SLA Metrics
        print("📊 Testando calculate_sla_metrics...")
        from app.services.os_metrics import calculate_sla_metrics

        sla_result = await calculate_sla_metrics([])
        print(f"   ✅ SLA com lista vazia: {sla_result}")

        # Teste 2: Equipment Status
        print("🔧 Testando calculate_equipment_status...")
        from app.services.equip_metrics import calculate_equipment_status

        active, inactive = await calculate_equipment_status([])
        print(f"   ✅ Equipamentos: {active} ativos, {inactive} inativos")

        # Teste 3: Maintenance Metrics
        print("⚙️ Testando calculate_maintenance_metrics...")
        from app.services.equip_metrics import calculate_maintenance_metrics

        maintenance_result = await calculate_maintenance_metrics([])
        print(f"   ✅ Manutenção: {maintenance_result}")

        # Teste 4: Technician KPIs
        print("👷 Testando calculate_technician_kpis...")
        from app.services.tech_metrics import calculate_technician_kpis
        from datetime import date

        kpi_result = await calculate_technician_kpis(1, "João", [], date.today(), date.today())
        print(f"   ✅ KPI Técnico: {kpi_result.name}")  # Usar 'name' que é o atributo correto

        print("\n🎉 TODOS OS TESTES PASSARAM!")
        return True

    except Exception as e:
        print(f"\n❌ ERRO: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Função principal para chamada externa."""
    return asyncio.run(test_services())


if __name__ == "__main__":
    success = asyncio.run(test_services())
    if success:
        print("\n✅ CONVERSÃO PARA ASYNC CONCLUÍDA COM SUCESSO!")
    else:
        print("\n⚠️ PROBLEMAS ENCONTRADOS - NECESSÁRIO REVISAR")
