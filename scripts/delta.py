#!/usr/bin/env python3
"""
Script CLI para executar sincronização incremental (delta).

Este script executa sincronização incremental apenas dos dados novos/modificados
desde a última sincronização.

Uso:
    poetry run python -m scripts.delta
    poetry run python -m scripts.delta --resources orders,equipments
    poetry run python -m scripts.delta --force-full
"""
import asyncio
import argparse
import sys
import time
from datetime import datetime, timedelta
from typing import List, Optional

# Configurar path para imports
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.sync.delta import run_incremental_sync, should_run_incremental_sync
from app.core.logging import app_logger
from app.core.db import init_database, get_database_info


class DeltaCLI:
    """Interface CLI para sincronização incremental."""

    def __init__(self):
        self.start_time: Optional[datetime] = None
        self.metrics = {
            "orders": {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0},
            "equipments": {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0},
            "technicians": {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0},
            "total_duration": 0.0,
            "last_sync_times": {},
        }

    def parse_args(self) -> argparse.Namespace:
        """Parse argumentos da linha de comando."""
        parser = argparse.ArgumentParser(
            description="Execute sincronização incremental (delta) de dados da API Arkmeds",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Exemplos:
  poetry run python -m scripts.delta
  poetry run python -m scripts.delta --resources orders
  poetry run python -m scripts.delta --force-full --verbose
  poetry run python -m scripts.delta --check-only
            """,
        )

        parser.add_argument(
            "--resources",
            type=str,
            default="orders,equipments,technicians",
            help="Recursos para sincronizar (separados por vírgula)",
        )

        parser.add_argument(
            "--force-full",
            action="store_true",
            help="Forçar sync completo mesmo se incremental estiver disponível",
        )

        parser.add_argument(
            "--check-only",
            action="store_true",
            help="Apenas verificar se sync é necessário (não executar)",
        )

        parser.add_argument("--verbose", "-v", action="store_true", help="Saída detalhada")

        parser.add_argument(
            "--min-interval",
            type=int,
            default=5,
            help="Intervalo mínimo entre syncs em minutos (padrão: 5)",
        )

        parser.add_argument(
            "--since",
            type=str,
            help="Sincronizar dados desde esta data (formato: YYYY-MM-DD ou YYYY-MM-DD HH:MM)",
        )

        return parser.parse_args()

    def print_header(self, args: argparse.Namespace) -> None:
        """Imprime cabeçalho do script."""
        print("=" * 60)
        print("🔄 SINCRONIZAÇÃO INCREMENTAL - Indicadores COMG")
        print("=" * 60)
        print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"📊 Recursos: {args.resources}")
        print(f"🔧 Modo: {'VERIFICAÇÃO' if args.check_only else 'EXECUÇÃO'}")
        print(f"⚡ Força completo: {'Sim' if args.force_full else 'Não'}")
        print(f"⏱️ Intervalo mín: {args.min_interval} minutos")
        if args.since:
            print(f"📅 Desde: {args.since}")
        print("=" * 60)
        print()

    def print_last_sync_info(self, resources: List[str]) -> None:
        """Imprime informações da última sincronização."""
        print("📊 ÚLTIMA SINCRONIZAÇÃO")
        print("-" * 30)

        try:
            from app.services.repository import get_database_stats

            stats = get_database_stats()

            # Mostrar informações de sync por recurso
            last_syncs = stats.get("last_syncs", [])

            for resource in resources:
                resource_sync = next((s for s in last_syncs if s["resource"] == resource), None)

                if resource_sync:
                    synced_at = resource_sync.get("synced_at")
                    if synced_at:
                        try:
                            sync_time = datetime.fromisoformat(synced_at)
                            delta = datetime.now() - sync_time
                            time_ago = self.format_timedelta(delta)
                            print(
                                f"📋 {resource}: {time_ago} ({sync_time.strftime('%d/%m %H:%M')})"
                            )
                        except:
                            print(f"📋 {resource}: {synced_at}")
                    else:
                        print(f"📋 {resource}: Nunca sincronizado")
                else:
                    print(f"📋 {resource}: Sem informações")

        except Exception as e:
            print(f"❌ Erro ao verificar última sincronização: {e}")

        print()

    def format_timedelta(self, delta: timedelta) -> str:
        """Formata timedelta de forma legível."""
        total_seconds = int(delta.total_seconds())

        if total_seconds < 60:
            return f"{total_seconds}s atrás"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes}min atrás"
        elif total_seconds < 86400:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h{minutes}min atrás"
        else:
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            return f"{days}d{hours}h atrás"

    def check_sync_necessity(self, resources: List[str], min_interval_minutes: int) -> dict:
        """Verifica se sync é necessário para cada recurso."""
        results = {}

        for resource in resources:
            try:
                is_needed = should_run_incremental_sync(resource, min_interval_minutes)
                results[resource] = {
                    "needed": is_needed,
                    "reason": "Intervalo atingido" if is_needed else "Muito recente",
                }
            except Exception as e:
                results[resource] = {"needed": True, "reason": f"Erro ao verificar: {e}"}

        return results

    def print_sync_check(self, check_results: dict) -> None:
        """Imprime resultado da verificação de necessidade."""
        print("🔍 VERIFICAÇÃO DE NECESSIDADE")
        print("-" * 30)

        for resource, result in check_results.items():
            status = "✅ NECESSÁRIO" if result["needed"] else "⏸️ AGUARDAR"
            print(f"{status} - {resource}: {result['reason']}")

        needed_count = sum(1 for r in check_results.values() if r["needed"])
        total_count = len(check_results)

        print(f"\n📊 Resumo: {needed_count}/{total_count} recursos precisam de sync")
        print()

    def start_timer(self) -> None:
        """Inicia cronômetro."""
        self.start_time = datetime.now()

    def get_elapsed_time(self) -> float:
        """Retorna tempo decorrido em segundos."""
        if not self.start_time:
            return 0.0
        return (datetime.now() - self.start_time).total_seconds()

    async def run_delta_sync(self, args: argparse.Namespace, resources: List[str]) -> bool:
        """Executa a sincronização incremental."""
        success = True

        for resource in resources:
            print(f"🔄 Sincronizando {resource}...")

            try:
                # Executar sync incremental
                result = await run_incremental_sync([resource])

                if result:
                    print(f"✅ {resource} sincronizado")

                    # Capturar métricas (simuladas - em produção vir do resultado)
                    self.metrics[resource]["inserted"] = result.get("inserted", 0)
                    self.metrics[resource]["updated"] = result.get("updated", 0)
                    self.metrics[resource]["skipped"] = result.get("skipped", 0)
                else:
                    print(f"⚠️ {resource} com avisos")
                    success = False

            except Exception as e:
                print(f"❌ Erro no sync de {resource}: {e}")
                self.metrics[resource]["errors"] += 1
                success = False
                app_logger.log_error(e, {"context": "cli_delta", "resource": resource})

        return success

    def print_metrics(self) -> None:
        """Imprime métricas finais."""
        duration = self.get_elapsed_time()
        self.metrics["total_duration"] = duration

        print("\n" + "=" * 60)
        print("📊 MÉTRICAS DE SINCRONIZAÇÃO INCREMENTAL")
        print("=" * 60)

        total_inserted = 0
        total_updated = 0
        total_skipped = 0
        total_errors = 0

        for resource, metrics in self.metrics.items():
            if resource in ["total_duration", "last_sync_times"]:
                continue

            inserted = metrics["inserted"]
            updated = metrics["updated"]
            skipped = metrics["skipped"]
            errors = metrics["errors"]

            print(f"📋 {resource.upper()}:")
            print(f"   ➕ Inseridos: {inserted}")
            print(f"   🔄 Atualizados: {updated}")
            print(f"   ⏭️ Ignorados: {skipped}")
            print(f"   ❌ Erros: {errors}")
            print()

            total_inserted += inserted
            total_updated += updated
            total_skipped += skipped
            total_errors += errors

        total_processed = total_inserted + total_updated + total_skipped

        print(f"🎯 TOTAIS:")
        print(f"   ➕ Total inseridos: {total_inserted}")
        print(f"   🔄 Total atualizados: {total_updated}")
        print(f"   ⏭️ Total ignorados: {total_skipped}")
        print(f"   ❌ Total erros: {total_errors}")
        print(f"   📦 Total processados: {total_processed}")
        print(f"   ⏱️ Tempo total: {duration:.2f}s")

        if duration > 0:
            rate = total_processed / duration
            print(f"   📊 Taxa: {rate:.2f} itens/s")

            # Eficiência (% de itens realmente modificados)
            if total_processed > 0:
                efficiency = ((total_inserted + total_updated) / total_processed) * 100
                print(f"   📈 Eficiência: {efficiency:.1f}% (modificados/processados)")

        print("=" * 60)

    async def run(self) -> int:
        """Executa o script principal."""
        try:
            # Parse argumentos
            args = self.parse_args()

            # Header
            self.print_header(args)

            # Verificar/inicializar banco
            print("🔧 Verificando banco de dados...")
            init_database()
            print("✅ Banco OK")
            print()

            # Parse recursos
            resources = [r.strip() for r in args.resources.split(",")]

            # Mostrar última sincronização
            self.print_last_sync_info(resources)

            # Verificar necessidade de sync
            check_results = self.check_sync_necessity(resources, args.min_interval)
            self.print_sync_check(check_results)

            # Se apenas verificação, parar aqui
            if args.check_only:
                needed = any(r["needed"] for r in check_results.values())
                return 0 if not needed else 1

            # Filtrar apenas recursos que precisam de sync (a menos que force)
            if not args.force_full:
                resources = [r for r in resources if check_results[r]["needed"]]

                if not resources:
                    print("✅ Nenhum recurso precisa de sincronização")
                    return 0

            # Iniciar timer
            self.start_timer()

            # Executar sincronização incremental
            print("🚀 Iniciando sincronização incremental...")
            print("-" * 40)

            success = await self.run_delta_sync(args, resources)

            # Métricas finais
            self.print_metrics()

            if success:
                print("\n🎉 Sincronização incremental concluída com sucesso!")
                return 0
            else:
                print("\n⚠️ Sincronização concluída com avisos/erros")
                return 1

        except KeyboardInterrupt:
            print("\n\n⏸️ Interrompido pelo usuário")
            return 130
        except Exception as e:
            print(f"\n❌ Erro fatal: {e}")
            app_logger.log_error(e, {"context": "cli_delta_main"})
            return 1


def main():
    """Ponto de entrada do script."""
    cli = DeltaCLI()
    exit_code = asyncio.run(cli.run())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
