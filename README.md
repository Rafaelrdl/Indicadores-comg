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

- Ordens de Serviço: `/api/v5/ordem_servico/`
- Chamados: `/api/v5/chamado/`
- Peças: `/api/v2/part/`

Caso sua instância utilize outra versão, ajuste a variável ``ARKMEDS_API_PREFIX``.

## Testes e qualidade de código

Execute as ferramentas abaixo para validar o estilo do código e rodar os testes
automatizados:

```bash
ruff check .      # verifica padrões de estilo
ruff format .     # formatação automática
pytest -q         # executa a suíte de testes
```
