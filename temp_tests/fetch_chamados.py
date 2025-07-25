#!/usr/bin/env python3
"""
Script para fazer requisição à API /api/v5/chamado/ e salvar resultado.
"""
import asyncio
import json
from datetime import datetime
from app.arkmeds_client.auth import ArkmedsAuth
from app.arkmeds_client.client import ArkmedsClient

async def fetch_chamados():
    """Faz requisição para /api/v5/chamado/ e salva resultado."""
    print("🔍 Fazendo requisição para /api/v5/chamado/...")
    
    auth = ArkmedsAuth.from_secrets()
    client = ArkmedsClient(auth)
    
    try:
        # Fazer requisição para o endpoint
        resp = await client._request("GET", "/api/v5/chamado/")
        data = resp.json()
        
        print(f"✅ Requisição bem-sucedida!")
        print(f"📊 Status: {resp.status_code}")
        print(f"📋 Dados recebidos: {len(str(data))} caracteres")
        
        # Preparar conteúdo para o arquivo Markdown
        timestamp = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
        
        content = f"""# Resultado da API /api/v5/chamado/

**Data da consulta:** {timestamp}  
**Endpoint:** `/api/v5/chamado/`  
**Status HTTP:** {resp.status_code}  
**Content-Type:** {resp.headers.get('content-type', 'N/A')}

## Estrutura da Resposta

```json
{json.dumps(data, indent=2, ensure_ascii=False)}
```

## Análise dos Dados

"""
        
        # Adicionar análise básica dos dados
        if isinstance(data, dict):
            if "count" in data:
                content += f"- **Total de registros:** {data.get('count', 'N/A')}\n"
            if "results" in data:
                results = data.get("results", [])
                content += f"- **Registros retornados:** {len(results)}\n"
                if results:
                    content += f"- **Estrutura do primeiro registro:**\n"
                    first_item = results[0]
                    for key, value in first_item.items():
                        content += f"  - `{key}`: {type(value).__name__}\n"
            if "next" in data:
                content += f"- **Próxima página:** {'Sim' if data.get('next') else 'Não'}\n"
            if "previous" in data:
                content += f"- **Página anterior:** {'Sim' if data.get('previous') else 'Não'}\n"
        elif isinstance(data, list):
            content += f"- **Tipo:** Lista com {len(data)} itens\n"
            if data:
                content += f"- **Estrutura do primeiro item:**\n"
                first_item = data[0]
                if isinstance(first_item, dict):
                    for key, value in first_item.items():
                        content += f"  - `{key}`: {type(value).__name__}\n"
        else:
            content += f"- **Tipo de resposta:** {type(data).__name__}\n"
        
        content += f"\n## Raw Response Headers\n\n"
        for header, value in resp.headers.items():
            content += f"- **{header}:** {value}\n"
        
        # Salvar no arquivo
        with open("resultado.md", "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"💾 Resultado salvo em 'resultado.md'")
        return data
        
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        
        # Salvar erro no arquivo também
        timestamp = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
        error_content = f"""# Erro na API /api/v5/chamado/

**Data da tentativa:** {timestamp}  
**Endpoint:** `/api/v5/chamado/`  

## Erro Encontrado

```
{str(e)}
```

## Detalhes do Erro

- **Tipo:** {type(e).__name__}
- **Mensagem:** {str(e)}

## Possíveis Causas

1. Endpoint não existe nesta versão da API
2. Permissões insuficientes 
3. Endpoint requer parâmetros específicos
4. Problema de conectividade

## Sugestões

- Verificar documentação da API
- Testar com parâmetros diferentes
- Verificar se endpoint existe em outra versão (/api/v3/chamado/)
"""
        
        with open("resultado.md", "w", encoding="utf-8") as f:
            f.write(error_content)
        
        print(f"💾 Erro salvo em 'resultado.md'")
        return None
        
    finally:
        await client.close()

async def main():
    try:
        result = await fetch_chamados()
        
        if result:
            print(f"\n✨ Consulta concluída com sucesso!")
            print(f"📄 Verifique o arquivo 'resultado.md' para detalhes completos")
        else:
            print(f"\n⚠️ Consulta falhou")
            print(f"📄 Verifique o arquivo 'resultado.md' para detalhes do erro")
            
    except Exception as e:
        print(f"💥 Erro geral: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
