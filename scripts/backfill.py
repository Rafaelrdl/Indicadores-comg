#!/usr/bin/env python3
"""
Script CLI para executar backfill completo dos dados.

Este script executa sincronização completa (backfill) de todos os recursos
da API Arkmeds para o banco SQLite local.

Uso:
    poetry run python -m scripts.backfill
    poetry run python -m scripts.backfill --resources orders,equipments
    poetry run python -m scripts.backfill --force
"""
import asyncio
import argparse
import sys
import time
from datetime import datetime
from typing import List, Optional

# Configurar path para imports
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.sync.ingest import run_backfill
from app.core.logging import app_logger
from app.core.db import init_database, get_database_info


class BackfillCLI:
    """Interface CLI para backfill de dados."""
    
    def __init__(self):
        self.start_time: Optional[datetime] = None
        self.metrics = {
            'orders': {'inserted': 0, 'updated': 0, 'errors': 0},
            'equipments': {'inserted': 0, 'updated': 0, 'errors': 0},
            'technicians': {'inserted': 0, 'updated': 0, 'errors': 0},
            'total_duration': 0.0
        }
    
    def parse_args(self) -> argparse.Namespace:
        """Parse argumentos da linha de comando."""
        parser = argparse.ArgumentParser(
            description="Execute backfill completo de dados da API Arkmeds",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Exemplos:
  poetry run python -m scripts.backfill
  poetry run python -m scripts.backfill --resources orders,equipments
  poetry run python -m scripts.backfill --force --verbose
  poetry run python -m scripts.backfill --dry-run
            """
        )
        
        parser.add_argument(
            '--resources', 
            type=str,
            default='orders,equipments,technicians',
            help='Recursos para sincronizar (separados por vírgula)'
        )
        
        parser.add_argument(
            '--force', 
            action='store_true',
            help='Forçar backfill mesmo com dados existentes'
        )
        
        parser.add_argument(
            '--dry-run', 
            action='store_true',
            help='Executar sem fazer mudanças (apenas mostrar o que seria feito)'
        )
        
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Saída detalhada'
        )
        
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Tamanho do batch para processamento (padrão: 100)'
        )
        
        return parser.parse_args()
    
    def print_header(self, args: argparse.Namespace) -> None:
        """Imprime cabeçalho do script."""
        print("=" * 60)
        print("🚀 BACKFILL COMPLETO - Indicadores COMG")
        print("=" * 60)
        print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"📊 Recursos: {args.resources}")
        print(f"🔧 Modo: {'DRY RUN' if args.dry_run else 'EXECUÇÃO'}")
        print(f"⚡ Força: {'Sim' if args.force else 'Não'}")
        print(f"📦 Batch size: {args.batch_size}")
        print("=" * 60)
        print()
    
    def print_database_status(self) -> None:
        """Imprime status atual do banco de dados."""
        print("📊 STATUS DO BANCO DE DADOS")
        print("-" * 30)
        
        try:
            db_info = get_database_info()
            
            if db_info.get('database_exists'):
                print(f"✅ Banco: {db_info['database_path']}")
                print(f"📏 Tamanho: {db_info.get('size_mb', 0):.2f} MB")
                
                # Contar registros por tabela
                from app.services.repository import get_database_stats
                stats = get_database_stats()
                
                print(f"📋 Ordens: {stats.get('orders_count', 0)} registros")
                print(f"⚙️ Equipamentos: {stats.get('equipments_count', 0)} registros") 
                print(f"👥 Técnicos: {stats.get('technicians_count', 0)} registros")
            else:
                print("⚠️ Banco de dados não inicializado")
                
        except Exception as e:
            print(f"❌ Erro ao verificar banco: {e}")
        
        print()
    
    def start_timer(self) -> None:
        """Inicia cronômetro."""
        self.start_time = datetime.now()
        
    def get_elapsed_time(self) -> float:
        """Retorna tempo decorrido em segundos."""
        if not self.start_time:
            return 0.0
        return (datetime.now() - self.start_time).total_seconds()
    
    async def run_backfill(self, args: argparse.Namespace) -> bool:
        """Executa o backfill."""
        if args.dry_run:
            print("🔍 MODO DRY RUN - Nenhuma mudança será feita")
            return True
        
        resources = [r.strip() for r in args.resources.split(',')]
        success = True
        
        for resource in resources:
            print(f"🔄 Iniciando backfill de {resource}...")
            
            try:
                result = await run_backfill([resource])
                
                if result:
                    print(f"✅ {resource} sincronizado com sucesso")
                    
                    # Simular métricas (em produção, capturar do resultado)
                    self.metrics[resource]['inserted'] = result.get('inserted', 0)
                    self.metrics[resource]['updated'] = result.get('updated', 0)
                else:
                    print(f"⚠️ {resource} com avisos")
                    success = False
                    
            except Exception as e:
                print(f"❌ Erro no backfill de {resource}: {e}")
                self.metrics[resource]['errors'] += 1
                success = False
                app_logger.log_error(e, {"context": "cli_backfill", "resource": resource})
        
        return success
    
    def print_metrics(self) -> None:
        """Imprime métricas finais."""
        duration = self.get_elapsed_time()
        self.metrics['total_duration'] = duration
        
        print("\n" + "=" * 60)
        print("📊 MÉTRICAS DE SINCRONIZAÇÃO")
        print("=" * 60)
        
        total_inserted = 0
        total_updated = 0
        total_errors = 0
        
        for resource, metrics in self.metrics.items():
            if resource == 'total_duration':
                continue
                
            inserted = metrics['inserted']
            updated = metrics['updated'] 
            errors = metrics['errors']
            
            print(f"📋 {resource.upper()}:")
            print(f"   ➕ Inseridos: {inserted}")
            print(f"   🔄 Atualizados: {updated}")
            print(f"   ❌ Erros: {errors}")
            print()
            
            total_inserted += inserted
            total_updated += updated
            total_errors += errors
        
        print(f"🎯 TOTAIS:")
        print(f"   ➕ Total inseridos: {total_inserted}")
        print(f"   🔄 Total atualizados: {total_updated}")
        print(f"   ❌ Total erros: {total_errors}")
        print(f"   ⏱️ Tempo total: {duration:.2f}s")
        print(f"   📊 Taxa: {(total_inserted + total_updated) / max(duration, 1):.2f} itens/s")
        print("=" * 60)
    
    async def run(self) -> int:
        """Executa o script principal."""
        try:
            # Parse argumentos
            args = self.parse_args()
            
            # Header
            self.print_header(args)
            
            # Verificar/inicializar banco
            print("🔧 Inicializando banco de dados...")
            init_database()
            print("✅ Banco inicializado")
            print()
            
            # Status do banco
            self.print_database_status()
            
            # Iniciar timer
            self.start_timer()
            
            # Executar backfill
            print("🚀 Iniciando sincronização...")
            print("-" * 40)
            
            success = await self.run_backfill(args)
            
            # Métricas finais
            self.print_metrics()
            
            if success:
                print("\n🎉 Backfill concluído com sucesso!")
                return 0
            else:
                print("\n⚠️ Backfill concluído com avisos/erros")
                return 1
                
        except KeyboardInterrupt:
            print("\n\n⏸️ Interrompido pelo usuário")
            return 130
        except Exception as e:
            print(f"\n❌ Erro fatal: {e}")
            app_logger.log_error(e, {"context": "cli_backfill_main"})
            return 1


def main():
    """Ponto de entrada do script."""
    cli = BackfillCLI()
    exit_code = asyncio.run(cli.run())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
