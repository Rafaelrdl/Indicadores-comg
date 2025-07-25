# Dashboard Arkmeds

![CI](https://github.com/Rafaelrdl/Indicadores-comg/actions/workflows/ci.yml/badge.svg)
![CD](https://github.com/Rafaelrdl/Indicadores-comg/actions/workflows/cd.yml/badge.svg)
![LOC](https://img.shields.io/tokei/lines/github/Rafaelrdl/Indicadores-comg)
![License](https://img.shields.io/github/license/Rafaelrdl/Indicadores-comg)

![Preview](docs/home_page.png)

## 📋 Visão Geral

Dashboard multipage em Streamlit para consolidar indicadores da plataforma Arkmeds.
Reúne ordens de serviço, equipamentos e produtividade em uma interface moderna e intuitiva.

### ✨ Características Principais
- **🏗️ Arquitetura Modular**: Componentes reutilizáveis e organizados
- **⚡ Performance Otimizada**: Sistema de cache inteligente
- **🎨 Interface Moderna**: Layout responsivo e profissional
- **📊 Análises Avançadas**: KPIs, métricas e visualizações
- **🔧 Fácil Manutenção**: Código limpo e bem documentado

## 🗂️ Estrutura do Projeto

```
├── 📱 app/                     # Aplicação principal
│   ├── core/                   # Infraestrutura central
│   ├── ui/                     # Componentes de interface
│   ├── services/               # Lógica de negócio
│   ├── arkmeds_client/         # Cliente da API
│   └── pages/                  # Páginas do dashboard
├── 📚 documentation/           # Documentação técnica
├── 🎨 assets/                  # Recursos visuais
├── 📊 data/                    # Dados e investigações
├── 🧪 tests/                   # Testes automatizados
├── 📜 scripts/                 # Scripts utilitários
└── 📖 docs/                    # Documentação do usuário
```

## 🚀 Requisitos

- Python 3.12+
- [Poetry](https://python-poetry.org/docs/#installation)

## ⚡ Quick Start

```bash
# 1. Configure variáveis locais
cp .env.example .env
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# 2. Edite as configurações
# .env ou .streamlit/secrets.toml:
# [arkmeds]
# base_url = "https://comg.arkmeds.com"
# (opcional) token = "seu_jwt_token_aqui"

# 3. Instale dependências e execute
poetry install --no-dev
poetry run streamlit run app/main.py
```

### 🖥️ Acesso Local
Após iniciar, acesse: `http://localhost:8501`

## 🛠️ Comandos Úteis

```bash
# Desenvolvimento
poetry install                          # Instala todas as dependências
poetry run streamlit run app/main.py    # Inicia o dashboard
poetry run python scripts/run_tests.py  # Executa testes

# Produção
poetry install --no-dev                 # Só dependências de produção
poetry run streamlit run app/main.py --server.port 8080
```

## 📚 Documentação

- **[📖 Documentação Técnica](./documentation/)** - Arquitetura e desenvolvimento
- **[🎨 Assets](./assets/)** - Recursos visuais e logos
- **[📊 Dados](./data/)** - Estruturas de dados e investigações
- **[🧪 Testes](./tests/)** - Estratégia e cobertura de testes

## 🎯 Funcionalidades

### 📊 Dashboards Disponíveis
1. **Ordens de Serviço** - Análise de chamados e SLA
2. **Equipamentos** - MTTR, MTBF e disponibilidade
3. **Técnicos** - Performance e produtividade da equipe

### 🔧 Componentes Principais
- **Métricas Interativas** - KPIs com visualização dinâmica
- **Tabelas Avançadas** - Filtros, paginação e exportação
- **Gráficos Responsivos** - Plotly integrado
- **Cache Inteligente** - Performance otimizada

## 📋 Boas Práticas

### 🗂️ Organização de Código
- Nomes de arquivo em `app/pages/` com caracteres ASCII
- Cada página define `st.set_page_config()`
- Componentes reutilizáveis em `app/ui/components/`
- Lógica de negócio isolada em `app/services/`

### 🔒 Segurança
- Nunca commite credenciais no código
- Use `.env` e `secrets.toml` para configurações
- Valide dados de entrada da API
- Mantenha dependências atualizadas

## 🤝 Contribuindo

1. **Fork** o repositório
2. **Crie** uma branch: `git checkout -b feature/nova-funcionalidade`
3. **Commit** suas mudanças: `git commit -m 'Adiciona nova funcionalidade'`
4. **Push** para a branch: `git push origin feature/nova-funcionalidade`
5. **Abra** um Pull Request

### 📝 Padrões de Commit
- `feat:` - Nova funcionalidade
- `fix:` - Correção de bug
- `docs:` - Documentação
- `style:` - Formatação
- `refactor:` - Refatoração
- `test:` - Testes

## 📄 Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE).

## Contato / Licenca

Projeto sob a [MIT License](LICENSE). Dúvidas abra uma issue.
<!-- Random comment for PR test -->
