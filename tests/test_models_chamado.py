#!/usr/bin/env python3
"""
Script para testar os novos modelos Chamado e ResponsavelTecnico
com dados reais da API /api/v5/chamado/.
"""

import asyncio
import json
from app.arkmeds_client.auth import ArkmedsAuth
from app.arkmeds_client.client import ArkmedsClient
from app.arkmeds_client.models import Chamado, ResponsavelTecnico


async def test_chamado_models():
    """Testa os novos modelos com dados reais."""
    print("🔍 Testando modelos Chamado e ResponsavelTecnico...")

    try:
        # Inicializar cliente
        auth = ArkmedsAuth.from_secrets()
        client = ArkmedsClient(auth)

        # Buscar alguns chamados para teste (limitado para não demorar)
        print("\n📡 Buscando chamados da API (limitado a 25 registros)...")
        chamados = await client.list_chamados({"page_size": 25, "page": 1})

        if not chamados:
            print("❌ Nenhum chamado encontrado")
            return

        print(f"✅ {len(chamados)} chamados encontrados")

        # Testar primeiro chamado
        chamado = chamados[0]
        print(f"\n📋 CHAMADO #{chamado.chamados}")
        print(f"  ID: {chamado.id}")
        print(f"  Arquivado: {chamado.chamado_arquivado}")
        print(f"  Status tempo: {chamado.status_tempo}")
        print(f"  Status fechamento: {chamado.status_fechamento}")
        print(f"  Finalizado sem atraso: {chamado.finalizado_sem_atraso}")
        print(f"  Finalizado com atraso: {chamado.finalizado_com_atraso}")
        print(f"  Número OS: {chamado.numero_os}")
        print(f"  Data criação OS: {chamado.data_criacao_os}")
        print(f"  Equipamento ID: {chamado.equipamento_id}")
        print(f"  Tipo serviço ID: {chamado.tipo_servico_id}")
        print(f"  Estado ID: {chamado.estado_id}")
        print(f"  Prioridade: {chamado.prioridade}")

        # Testar responsável técnico
        if chamado.get_resp_tecnico:
            resp = chamado.get_resp_tecnico
            print(f"\n👤 RESPONSÁVEL TÉCNICO")
            print(f"  ID: {resp.id} (int: {resp.id_int})")
            print(f"  Nome: {resp.nome}")
            print(f"  Email: {resp.email}")
            print(f"  Has avatar: {resp.has_avatar}")
            print(f"  Avatar: {resp.avatar}")
            print(f"  Display name: {resp.display_name}")
            print(f"  Avatar display: {resp.avatar_display}")
            print(f"  String representation: {str(resp)}")

        print(f"\n🔗 String representation do chamado: {str(chamado)}")

        # Testar responsáveis únicos (limitado aos chamados já buscados)
        print("\n👥 Extraindo responsáveis técnicos únicos dos chamados buscados...")
        responsaveis = await client.list_responsaveis_tecnicos({"page_size": 25, "page": 1})
        print(f"✅ {len(responsaveis)} responsáveis únicos encontrados:")

        for resp in responsaveis:
            print(f"  - {resp.display_name} (ID: {resp.id})")
            if resp.has_avatar and resp.avatar and resp.avatar.startswith("http"):
                print(f"    Avatar: {resp.avatar[:60]}...")

        # Estatísticas de chamados
        print(f"\n📊 ESTATÍSTICAS DOS {len(chamados)} CHAMADOS:")
        arquivados = sum(1 for c in chamados if c.chamado_arquivado)
        sem_atraso = sum(1 for c in chamados if c.finalizado_sem_atraso)
        com_atraso = sum(1 for c in chamados if c.finalizado_com_atraso)
        vazios = sum(1 for c in chamados if c.status_tempo == "vazio")

        print(f"  - Arquivados: {arquivados}")
        print(f"  - Finalizados sem atraso: {sem_atraso}")
        print(f"  - Finalizados com atraso: {com_atraso}")
        print(f"  - Status vazio: {vazios}")

        # Tipos de serviço mais comuns
        tipos_servico = {}
        for c in chamados:
            tipo_id = c.tipo_servico_id
            if tipo_id:
                tipos_servico[tipo_id] = tipos_servico.get(tipo_id, 0) + 1

        print(f"\n🔧 TIPOS DE SERVIÇO MAIS COMUNS:")
        for tipo_id, count in sorted(tipos_servico.items(), key=lambda x: x[1], reverse=True):
            print(f"  - Tipo {tipo_id}: {count} chamados")

        print("\n✅ Teste dos modelos concluído com sucesso!")

    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_chamado_models())
