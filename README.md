# Indicadores COMG

Projeto para cálculo e visualização de indicadores de manutenção.

## Pré-requisitos

- Python 3.11 ou superior

## Instalação

Clone o repositório e instale as dependências do projeto:

```bash
pip install -r requirements.txt
```

## Execução da aplicação

1. Defina as variáveis de ambiente da API Arkmeds (pode ser em um arquivo `.env`
   na raiz do projeto ou em `.streamlit/secrets.toml`):

   ```bash
   ARKMEDS_EMAIL=<seu-email>
   ARKMEDS_PASSWORD=<sua-senha>
   # Opcional: informe um token obtido previamente
   ARKMEDS_TOKEN=<seu-token>
   BASE_URL=https://<slug>.arkmeds.com
   # Opcional quando ``BASE_URL`` não inclui o prefixo
   ARKMEDS_API_PREFIX=/api/v5   # deixe vazio se ``BASE_URL`` já inclui o prefixo
   ```

   Você pode definir ``BASE_URL`` de duas formas:

   1. ``BASE_URL=https://<slug>.arkmeds.com/api/v5``
   2. ``BASE_URL=https://<slug>.arkmeds.com`` e ``ARKMEDS_API_PREFIX=/api/v5``

2. Inicie a aplicação via Streamlit:

   ```bash

   streamlit run presentation/streamlit_app.py
   ```

## Endpoints principais

| Rota | Versão |
|------|--------|
| `/api/v5/ordem_servico/` | v5 |
| `/api/v5/chamado/` | v5 |
| `/api/v5/oficina/` | v5 |
| `/api/v5/company/` | v5 |
| `/api/v5/company/{id}` | v5 |
| `/api/v5/company/equipaments/` | v5 |
| `/api/v5/equipament/{id}` | v5 |
| `/api/v4/servico_orcamento/` | v4 |
| `/api/v3/estado_ordem_servico/` | v3 |
| `/api/v3/origem_problema/` | v3 |
| `/api/v3/problema_relatado/` | v3 |
| `/api/v3/tipo_servico/` | v3 |
| `/api/v2/part_type/` | v2 |
| `/api/v2/part/` | v2 |
| `/api/v2/part_item/` | v2 |
| `/api/v2/company/` | v2 |

Novas rotas podem ser incluídas editando o dicionário ``ROUTES`` em
`infrastructure/arkmeds_client.py`.

Caso sua instância utilize outra versão, ajuste a variável ``ARKMEDS_API_PREFIX``.

## Testes e qualidade de código

Execute as ferramentas abaixo para validar o estilo do código e rodar os testes
automatizados:

```bash
ruff check .      # verifica padrões de estilo
ruff format .     # formatação automática
pytest -q         # executa a suíte de testes
```
