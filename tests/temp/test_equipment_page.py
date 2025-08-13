#!/usr/bin/env python3
"""
Teste específico para a página de equipamentos atualizada.
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório app ao path
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))


async def test_equipment_page():
    """Testa as funcionalidades da página de equipamentos."""
    print("🧪 Testando funcionalidades da página de equipamentos...")

    try:
        from arkmeds_client.auth import ArkmedsAuth
        from arkmeds_client.client import ArkmedsClient
        from services.equip_advanced_metrics import calcular_stats_equipamentos

        # Inicializar cliente
        auth = ArkmedsAuth.from_secrets()
        client = ArkmedsClient(auth)

        print("1️⃣ Testando busca de equipamentos...")
        equipamentos = await client.list_equipamentos()
        print(f"   ✅ Encontrados {len(equipamentos)} equipamentos")

        print("2️⃣ Testando cálculo de estatísticas...")

        # Teste inline das estatísticas (sem streamlit cache)
        async def _calc_stats():
            equipamentos = await client.list_equipamentos()

            # Contadores básicos
            prioridades = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, None: 0}
            ativos = 0
            desativados = 0

            for equip in equipamentos:
                prioridade = equip.prioridade
                if prioridade in prioridades:
                    prioridades[prioridade] += 1
                else:
                    prioridades[None] += 1

                if getattr(equip, "ativo", True):
                    ativos += 1
                else:
                    desativados += 1

            return {
                "prioridades": prioridades,
                "ativos": ativos,
                "desativados": desativados,
                "total": len(equipamentos),
            }

        stats = await _calc_stats()
        print(f"   ✅ Estatísticas calculadas:")
        print(f"      - Total: {stats['total']} equipamentos")
        print(f"      - Ativos: {stats['ativos']}")
        print(f"      - Desativados: {stats['desativados']}")
        print(f"      - Prioridades: {stats['prioridades']}")

        print("3️⃣ Testando busca de chamados...")
        from datetime import date, timedelta

        data_limite = date.today() - timedelta(days=30)

        chamados = await client.list_chamados(
            {
                "data_criacao__gte": data_limite,
            }
        )
        print(f"   ✅ Encontrados {len(chamados)} chamados dos últimos 30 dias")

        if chamados:
            # Verificar estrutura de um chamado
            chamado = chamados[0]
            print(f"   📋 Exemplo de chamado #{chamado.chamados}:")
            print(f"      - Equipamento ID: {chamado.equipamento_id}")
            print(f"      - Data criação: {chamado.data_criacao_os}")
            print(f"      - Responsável: {chamado.responsavel_nome}")

        print("4️⃣ Testando agrupamento por equipamento...")
        from collections import defaultdict

        chamados_por_equip = defaultdict(list)
        for chamado in chamados:
            if chamado.equipamento_id:
                chamados_por_equip[chamado.equipamento_id].append(chamado)

        equipamentos_com_chamados = len(chamados_por_equip)
        total_equipamentos_sample = min(5, len(chamados_por_equip))

        print(f"   ✅ {equipamentos_com_chamados} equipamentos têm chamados")
        print(f"   📊 Amostra de equipamentos com mais chamados:")

        # Top equipamentos por número de chamados
        top_equips = sorted(chamados_por_equip.items(), key=lambda x: len(x[1]), reverse=True)[
            :total_equipamentos_sample
        ]

        for equip_id, chamados_list in top_equips:
            # Buscar nome do equipamento
            equip_nome = "N/A"
            for eq in equipamentos:
                if eq.id == equip_id:
                    equip_nome = eq.display_name
                    break

            print(f"      - Equipamento {equip_id} ({equip_nome}): {len(chamados_list)} chamados")

        print("\n✅ Todos os testes da página de equipamentos passaram!")

    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_equipment_page())
