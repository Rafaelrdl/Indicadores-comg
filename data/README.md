# 📊 Dados do Projeto

Esta pasta contém arquivos de dados, configurações e recursos de investigação do projeto Indicadores-COMG.

## 📁 Conteúdo

### 🔍 Investigações e Análises
- **[equipments_api_investigation.json](./equipments_api_investigation.json)** - Dados de investigação da API de equipamentos

## 📋 Tipos de Dados

### Investigações (`.json`)
Arquivos com dados coletados durante investigações e análises:
- Respostas de APIs
- Estruturas de dados descobertas
- Configurações de teste

### Configurações (`.yml`, `.json`)
Arquivos de configuração para diferentes ambientes:
- Configurações de desenvolvimento
- Parâmetros de produção
- Mapeamentos de dados

### Samples (`.csv`, `.json`)
Dados de exemplo para testes e desenvolvimento:
- Dados de teste
- Estruturas de exemplo
- Mocks para desenvolvimento

## 🗂️ Organização Sugerida

```
data/
├── investigations/     # Dados de investigação
├── configs/           # Arquivos de configuração
├── samples/           # Dados de exemplo
├── exports/           # Dados exportados
└── temp/              # Arquivos temporários
```

## 🔒 Segurança

### ⚠️ Dados Sensíveis
- **NÃO** commite dados de produção
- Use `.env` para credenciais
- Mascare dados pessoais em samples
- Mantenha backups seguros

### 📝 Boas Práticas
- Use dados anonimizados para testes
- Documente a origem dos dados
- Mantenha versionamento de configurações
- Implemente validação de esquemas

## 🛠️ Uso na Aplicação

### Carregar Investigações
```python
import json

with open('data/equipments_api_investigation.json', 'r') as f:
    investigation_data = json.load(f)
```

### Configurações
```python
from pathlib import Path
import yaml

config_path = Path('data/configs/app.yml')
with open(config_path) as f:
    config = yaml.safe_load(f)
```

## 📝 Manutenção

- Mantenha dados organizados por tipo
- Remova arquivos temporários periodicamente
- Documente mudanças em estruturas de dados
- Use gitignore para dados sensíveis

---

*Última atualização: 25 de julho de 2025*
