#!/usr/bin/env python3
"""
Teste dos comandos CLI (backfill e delta).

Este script valida que os comandos CLI funcionam corretamente
e produzem as métricas esperadas.
"""
import subprocess
import sys
import os

def run_command(cmd: list, description: str) -> tuple[bool, str, str]:
    """Executa comando e retorna resultado."""
    print(f"🧪 Testando: {description}")
    print(f"   Comando: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=60,
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        success = result.returncode == 0
        stdout = result.stdout
        stderr = result.stderr
        
        if success:
            print(f"   ✅ Sucesso (código: {result.returncode})")
        else:
            print(f"   ❌ Falhou (código: {result.returncode})")
            if stderr:
                print(f"   Erro: {stderr[:200]}...")
        
        return success, stdout, stderr
        
    except subprocess.TimeoutExpired:
        print(f"   ⏰ Timeout após 60 segundos")
        return False, "", "Timeout"
    except Exception as e:
        print(f"   💥 Exceção: {e}")
        return False, "", str(e)

def test_cli_help():
    """Testa comandos de help."""
    print("📋 TESTANDO COMANDOS DE HELP")
    print("-" * 40)
    
    commands = [
        (["poetry", "run", "python", "-m", "scripts.backfill", "--help"], "Backfill Help"),
        (["poetry", "run", "python", "-m", "scripts.delta", "--help"], "Delta Help"),
    ]
    
    passed = 0
    total = len(commands)
    
    for cmd, desc in commands:
        success, stdout, stderr = run_command(cmd, desc)
        if success and "usage:" in stdout:
            passed += 1
        print()
    
    return passed, total

def test_cli_dry_runs():
    """Testa execuções dry-run."""
    print("🔍 TESTANDO EXECUÇÕES DRY-RUN")
    print("-" * 40)
    
    commands = [
        (["poetry", "run", "python", "-m", "scripts.backfill", "--dry-run", "--resources", "orders"], "Backfill Dry-Run"),
        (["poetry", "run", "python", "-m", "scripts.delta", "--check-only"], "Delta Check-Only"),
    ]
    
    passed = 0
    total = len(commands)
    
    for cmd, desc in commands:
        success, stdout, stderr = run_command(cmd, desc)
        if success and ("DRY RUN" in stdout or "VERIFICAÇÃO" in stdout):
            passed += 1
        print()
    
    return passed, total

def test_cli_metrics():
    """Testa se métricas são exibidas."""
    print("📊 TESTANDO MÉTRICAS DOS SCRIPTS")
    print("-" * 40)
    
    commands = [
        (["poetry", "run", "python", "-m", "scripts.backfill", "--dry-run"], "Backfill Metrics"),
        (["poetry", "run", "python", "-m", "scripts.delta", "--check-only"], "Delta Metrics"),
    ]
    
    passed = 0
    total = len(commands)
    
    for cmd, desc in commands:
        success, stdout, stderr = run_command(cmd, desc)
        # Verificar se métricas estão presentes
        has_metrics = any(keyword in stdout for keyword in [
            "MÉTRICAS", "Total inseridos", "Total atualizados", "Tempo total"
        ])
        
        if success and has_metrics:
            passed += 1
            print(f"   📈 Métricas detectadas")
        elif success:
            print(f"   ⚠️ Comando executou mas métricas não detectadas")
        
        print()
    
    return passed, total

def test_cli_error_handling():
    """Testa tratamento de erros."""
    print("⚠️ TESTANDO TRATAMENTO DE ERROS")
    print("-" * 40)
    
    commands = [
        (["poetry", "run", "python", "-m", "scripts.backfill", "--resources", "invalid_resource"], "Invalid Resource"),
        (["poetry", "run", "python", "-m", "scripts.delta", "--since", "invalid_date"], "Invalid Date"),
    ]
    
    passed = 0
    total = len(commands)
    
    for cmd, desc in commands:
        success, stdout, stderr = run_command(cmd, desc)
        # Para testes de erro, esperamos falha controlada ou mensagem de erro
        has_error_handling = any(keyword in stdout.lower() for keyword in [
            "erro", "error", "inválido", "invalid", "falha"
        ])
        
        if not success or has_error_handling:
            passed += 1
            print(f"   ✅ Erro tratado adequadamente")
        else:
            print(f"   ❌ Erro não foi tratado")
        
        print()
    
    return passed, total

def main():
    """Executa todos os testes de CLI."""
    print("🚀 TESTE DOS COMANDOS CLI - Indicadores COMG")
    print("=" * 60)
    print()
    
    # Verificar se estamos no diretório correto
    if not os.path.exists("scripts/backfill.py"):
        print("❌ Execute este script a partir do diretório raiz do projeto")
        return 1
    
    total_passed = 0
    total_tests = 0
    
    # Executar conjuntos de testes
    test_suites = [
        test_cli_help,
        test_cli_dry_runs,
        test_cli_metrics,
        test_cli_error_handling,
    ]
    
    for test_suite in test_suites:
        passed, total = test_suite()
        total_passed += passed
        total_tests += total
        
        print(f"📊 Resultado: {passed}/{total} testes passaram")
        print()
    
    # Resumo final
    print("=" * 60)
    print(f"🎯 RESULTADO FINAL: {total_passed}/{total_tests} testes passaram")
    
    if total_passed == total_tests:
        print("🎉 Todos os comandos CLI funcionam corretamente!")
        print("✅ Scripts prontos para uso em produção")
        return 0
    else:
        print("⚠️ Alguns testes falharam")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
