#!/usr/bin/env python3
"""
Script para executar linting e formatação completa no projeto Indicadores-comg.

Usage:
    python scripts/lint.py [--fix] [--check-only]

Arguments:
    --fix: Aplicar correções automáticas do Ruff
    --check-only: Apenas verificar sem aplicar mudanças
"""

import subprocess
import sys
from pathlib import Path

# Diretórios para lint
LINT_DIRS = ["app", "tests", "scripts"]


def run_command(cmd: list[str], description: str) -> bool:
    """Execute um comando e retorna True se bem-sucedido."""
    print(f"\n🔧 {description}...")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ {description} - OK")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} - FALHOU")
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            return False

    except FileNotFoundError:
        print(f"❌ Comando não encontrado: {cmd[0]}")
        return False


def main():
    """Função principal do script de linting."""
    check_only = "--check-only" in sys.argv
    apply_fixes = "--fix" in sys.argv and not check_only

    print("🚀 Iniciando processo de linting...")
    print(f"Diretórios: {', '.join(LINT_DIRS)}")

    success = True

    # 1. Ruff check
    ruff_cmd = ["ruff", "check"] + LINT_DIRS
    if apply_fixes:
        ruff_cmd.append("--fix")

    success &= run_command(ruff_cmd, "Ruff linting")

    # 2. Black formatting
    if check_only:
        black_cmd = ["black", "--check", "--diff"] + LINT_DIRS
        success &= run_command(black_cmd, "Black formatting check")
    else:
        black_cmd = ["black"] + LINT_DIRS
        success &= run_command(black_cmd, "Black formatting")

    # 3. Resultado final
    print("\n" + "=" * 50)
    if success:
        print("✅ LINTING COMPLETO - Tudo OK!")
    else:
        print("❌ LINTING FALHOU - Verifique os erros acima")
        sys.exit(1)


if __name__ == "__main__":
    main()
