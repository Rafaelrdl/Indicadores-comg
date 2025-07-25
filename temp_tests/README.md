# Arquivos Temporários de Teste

Esta pasta contém scripts temporários criados durante o processo de auditoria e desenvolvimento do projeto.

## Conteúdo

### Scripts de Auditoria da API
- `temp_audit_estados.py` - Auditoria dos estados de OS
- `temp_discover_tipos.py` - Descoberta dos tipos de serviço
- `temp_check_estados.py` - Verificação de estados
- `temp_check_users.py` - Verificação de usuários
- `temp_find_users.py` - Busca de usuários

### Scripts de Teste
- `test_user_simple.py` - Teste simples de usuários
- `test_final.py` - Teste final
- `temp_test_user.py` - Teste temporário de usuário

### Scripts de Coleta de Dados
- `fetch_chamados.py` - Script para buscar dados de chamados da API

## Status

⚠️ **ARQUIVOS TEMPORÁRIOS** - Estes arquivos foram criados para investigação e podem ser removidos após a consolidação dos modelos principais.

## Limpeza

Para limpar estes arquivos temporários:
```powershell
Remove-Item temp_tests\* -Force
```

**NOTA:** Mantenha apenas se precisar referenciar alguma lógica específica dos scripts de auditoria.
