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
   BASE_URL=https://api-os.arkmeds.com
   ```

   Para apontar para ambientes de staging ou produção, altere o valor de
   `BASE_URL` conforme necessário.

2. Inicie a aplicação via Streamlit:

   ```bash
   streamlit run presentation/streamlit_app.py
   ```

## Testes e qualidade de código

Execute as ferramentas abaixo para validar o estilo do código e rodar os testes
automatizados:

```bash
ruff check .      # verifica padrões de estilo
ruff format .     # formatação automática
pytest -q         # executa a suíte de testes
```
