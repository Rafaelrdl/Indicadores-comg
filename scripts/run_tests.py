#!/usr/bin/env python
"""Script para executar testes da aplicação."""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(command: list, description: str) -> bool:
    """Executa comando e retorna sucesso/falha."""
    print(f"\n🔄 {description}...")
    print(f"Executando: {' '.join(command)}")
    
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Sucesso")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Falha")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Executar testes da aplicação")
    parser.add_argument("--type", choices=["all", "unit", "integration"], default="all",
                       help="Tipo de testes a executar")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Saída verbosa")
    parser.add_argument("--coverage", "-c", action="store_true",
                       help="Executar com cobertura de código")
    
    args = parser.parse_args()
    
    # Mudar para diretório app
    app_dir = Path(__file__).parent / "app"
    print(f"📁 Mudando para diretório: {app_dir}")
    
    success = True
    
    if args.type in ["all", "unit"]:
        # Testes unitários
        command = ["python", "-m", "pytest", "../tests/unit/"]
        if args.verbose:
            command.append("-v")
        if args.coverage:
            command.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
        
        success &= run_command(command, "Testes Unitários")
    
    if args.type in ["all", "integration"]:
        # Testes de integração (quando existirem)
        integration_dir = Path("../tests/integration/")
        if integration_dir.exists():
            command = ["python", "-m", "pytest", "../tests/integration/"]
            if args.verbose:
                command.append("-v")
            
            success &= run_command(command, "Testes de Integração")
        else:
            print("ℹ️ Testes de integração ainda não implementados")
    
    # Lint com ruff (se disponível)
    try:
        command = ["python", "-m", "ruff", "check", "."]
        run_command(command, "Análise de Código (Ruff)")
    except FileNotFoundError:
        print("ℹ️ Ruff não encontrado, pulando análise de código")
    
    # Resultado final
    if success:
        print("\n🎉 Todos os testes passaram!")
        sys.exit(0)
    else:
        print("\n💥 Alguns testes falharam!")
        sys.exit(1)


if __name__ == "__main__":
    main()
