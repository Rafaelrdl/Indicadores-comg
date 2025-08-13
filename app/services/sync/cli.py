"""
Comandos de linha para sincronização manual de dados.
"""

import argparse
import asyncio
from datetime import date, timedelta

from app.arkmeds_client.auth import ArkmedsAuth
from app.arkmeds_client.client import ArkmedsClient
from app.core.config import get_settings
from app.core.db import init_database
from app.services.sync.delta import run_incremental_sync
from app.services.sync.ingest import run_backfill


async def main() -> None:
    """Função principal do CLI."""
    parser = argparse.ArgumentParser(description="Sincronização de dados Arkmeds")

    # Comandos principais
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Comando backfill
    backfill_parser = subparsers.add_parser("backfill", help="Sincronização completa (backfill)")
    backfill_parser.add_argument(
        "--resources",
        nargs="+",
        choices=["orders", "equipments", "technicians"],
        default=["orders"],
        help="Recursos para sincronizar",
    )
    backfill_parser.add_argument(
        "--start-date", type=str, help="Data inicial (YYYY-MM-DD, apenas para orders)"
    )
    backfill_parser.add_argument(
        "--end-date", type=str, help="Data final (YYYY-MM-DD, apenas para orders)"
    )

    # Comando incremental
    incremental_parser = subparsers.add_parser("incremental", help="Sincronização incremental")
    incremental_parser.add_argument(
        "--resources",
        nargs="+",
        choices=["orders", "equipments", "technicians"],
        default=["orders"],
        help="Recursos para sincronizar",
    )

    # Comando sync (automático)
    sync_parser = subparsers.add_parser(
        "sync", help="Sincronização inteligente (incremental + fallback)"
    )
    sync_parser.add_argument(
        "--resources",
        nargs="+",
        choices=["orders", "equipments", "technicians"],
        default=["orders"],
        help="Recursos para sincronizar",
    )
    sync_parser.add_argument(
        "--force-backfill", action="store_true", help="Forçar backfill completo"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Inicializar banco
    init_database()

    # Configurar cliente da API
    settings = get_settings()
    auth = ArkmedsAuth(
        base_url=settings.api_base_url,
        username=settings.api_username,
        password=settings.api_password,
    )

    client = ArkmedsClient(auth=auth)

    try:
        if args.command == "backfill":
            await handle_backfill(client, args)
        elif args.command == "incremental":
            await handle_incremental(client, args)
        elif args.command == "sync":
            await handle_smart_sync(client, args)

    except KeyboardInterrupt:
        print("\n❌ Operação cancelada pelo usuário")
    except Exception as e:
        print(f"❌ Erro durante sincronização: {e}")


async def handle_backfill(client: ArkmedsClient, args) -> None:
    """Executa backfill completo."""
    print(f"🚀 Iniciando backfill para recursos: {', '.join(args.resources)}")

    # Processar datas se fornecidas
    start_date = None
    end_date = None

    if args.start_date:
        start_date = date.fromisoformat(args.start_date)
    if args.end_date:
        end_date = date.fromisoformat(args.end_date)

    # Executar backfill
    results = await run_backfill(
        client, resources=args.resources, start_date=start_date, end_date=end_date
    )

    # Mostrar resultados
    print("\n📊 Resultados do backfill:")
    for resource, count in results.items():
        print(f"  {resource}: {count:,} registros")

    total = sum(results.values())
    print(f"\n✅ Total: {total:,} registros sincronizados")


async def handle_incremental(client: ArkmedsClient, args) -> None:
    """Executa sincronização incremental."""
    print(f"🔄 Iniciando sincronização incremental para recursos: {', '.join(args.resources)}")

    # Executar sync incremental
    results = await run_incremental_sync(client, resources=args.resources)

    # Mostrar resultados
    print("\n📊 Resultados da sincronização incremental:")
    for resource, count in results.items():
        print(f"  {resource}: {count:,} novos registros")

    total = sum(results.values())
    print(f"\n✅ Total: {total:,} novos registros sincronizados")


async def handle_smart_sync(client: ArkmedsClient, args) -> None:
    """Executa sincronização inteligente."""
    from app.services.sync.delta import should_run_incremental_sync

    print(f"🧠 Iniciando sincronização inteligente para recursos: {', '.join(args.resources)}")

    results = {}

    for resource in args.resources:
        print(f"\n📋 Processando {resource}...")

        if args.force_backfill or not should_run_incremental_sync(resource):
            print(f"  🔄 Executando backfill para {resource}")

            if resource == "orders":
                # Para orders, fazer backfill dos últimos 30 dias por padrão
                end_date = date.today()
                start_date = end_date - timedelta(days=30)
                backfill_results = await run_backfill(
                    client, [resource], start_date=start_date, end_date=end_date
                )
            else:
                backfill_results = await run_backfill(client, [resource])

            results[resource] = backfill_results.get(resource, 0)

        else:
            print(f"  ⚡ Executando sincronização incremental para {resource}")
            incremental_results = await run_incremental_sync(client, [resource])
            results[resource] = incremental_results.get(resource, 0)

        # Pausa entre recursos
        await asyncio.sleep(1)

    # Mostrar resultados
    print("\n📊 Resultados da sincronização inteligente:")
    for resource, count in results.items():
        print(f"  {resource}: {count:,} registros")

    total = sum(results.values())
    print(f"\n✅ Total: {total:,} registros sincronizados")


if __name__ == "__main__":
    asyncio.run(main())
