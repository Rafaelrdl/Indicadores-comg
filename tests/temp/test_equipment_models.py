#!/usr/bin/env python3
"""
Script de teste para validar os novos modelos Equipment e Company.

Testa:
- Busca de empresas com equipamentos
- Busca de equipamentos individuais
- Propriedades calculadas dos modelos
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório app ao path
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

from arkmeds_client.auth import ArkmedsAuth
from arkmeds_client.client import ArkmedsClient
from arkmeds_client.models import Company, Equipment


async def main():
    print("🧪 Testando novos modelos Equipment e Company...")
    print("=" * 60)

    # Autenticação
    auth = ArkmedsAuth.from_secrets()
    client = ArkmedsClient(auth)

    try:
        # 1. Testar busca de empresas
        print("\n1️⃣ Testando busca de empresas...")
        companies = await client.list_companies_equipamentos()
        print(f"   ✅ Encontradas {len(companies)} empresas")

        if companies:
            # Mostrar primeira empresa como exemplo
            company = companies[0]
            print(f"   📋 Primeira empresa: {company}")
            print(f"   🏢 Nome fantasia: {company.display_name}")
            print(f"   📍 Endereço: {company.endereco_completo}")
            print(f"   ⚙️ Total equipamentos: {company.total_equipamentos}")

        # 2. Testar busca de equipamentos
        print("\n2️⃣ Testando busca de equipamentos...")
        equipamentos = await client.list_equipamentos()
        print(f"   ✅ Encontrados {len(equipamentos)} equipamentos")

        if equipamentos:
            # Mostrar primeiro equipamento como exemplo
            equip = equipamentos[0]
            print(f"   🔧 Primeiro equipamento: {equip}")
            print(f"   📝 Nome display: {equip.display_name}")
            print(f"   📄 Descrição completa: {equip.descricao_completa}")
            print(f"   ⚠️ Criticidade: {equip.criticidade_nivel}")
            print(f"   🎯 Prioridade: {equip.prioridade_nivel}")

            # Testar busca individual
            print(f"\n3️⃣ Testando busca individual do equipamento {equip.id}...")
            equip_individual = await client.get_equipamento(equip.id)
            if equip_individual:
                print(f"   ✅ Equipamento encontrado: {equip_individual.display_name}")
            else:
                print(f"   ❌ Equipamento não encontrado")

        # 3. Estatísticas gerais
        print(f"\n📊 ESTATÍSTICAS GERAIS:")
        print(f"   - Total de empresas: {len(companies)}")
        print(f"   - Total de equipamentos: {len(equipamentos)}")

        if companies and equipamentos:
            # Equipamentos por empresa
            empresa_equips = {}
            for company in companies:
                empresa_equips[company.display_name] = company.total_equipamentos

            # Top 5 empresas com mais equipamentos
            top_empresas = sorted(empresa_equips.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"\n🏆 TOP 5 EMPRESAS COM MAIS EQUIPAMENTOS:")
            for i, (nome, total) in enumerate(top_empresas, 1):
                print(f"   {i}. {nome}: {total} equipamentos")

            # Estatísticas de criticidade
            criticidades = {}
            for equip in equipamentos:
                nivel = equip.criticidade_nivel
                criticidades[nivel] = criticidades.get(nivel, 0) + 1

            print(f"\n⚠️ DISTRIBUIÇÃO DE CRITICIDADE:")
            for nivel, count in sorted(criticidades.items()):
                print(f"   - {nivel}: {count} equipamentos")

            # Estatísticas de prioridade
            prioridades = {}
            for equip in equipamentos:
                nivel = equip.prioridade_nivel
                prioridades[nivel] = prioridades.get(nivel, 0) + 1

            print(f"\n🎯 DISTRIBUIÇÃO DE PRIORIDADE:")
            for nivel, count in sorted(prioridades.items()):
                print(f"   - {nivel}: {count} equipamentos")

        print(f"\n✅ Teste concluído com sucesso!")

    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
