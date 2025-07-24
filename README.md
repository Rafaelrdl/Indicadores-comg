# Dashboard Arkmeds

![CI](https://github.com/<OWNER>/<REPO>/actions/workflows/ci.yml/badge.svg)
![CD](https://github.com/<OWNER>/<REPO>/actions/workflows/cd.yml/badge.svg)
![LOC](https://img.shields.io/tokei/lines/github/<OWNER>/<REPO>)
![License](https://img.shields.io/github/license/<OWNER>/<REPO>)

![Preview](docs/home_page.png)

## Visao Geral

Dashboard multipage em Streamlit para consolidar indicadores da plataforma Arkmeds.
Reúne ordens de serviço, equipamentos e produtividade em uma interface simples.

## Requisitos

- Python 3.12+
- [Poetry](https://python-poetry.org/docs/#installation)

## Quick Start

```bash
# configure variáveis locais
cp .env.example .env
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edite a base_url incluindo o protocolo
# Exemplo:
# [arkmeds]
# base_url = "https://comg.arkmeds.com"
# se já possuir um JWT válido, defina `token` para evitar login
# O endpoint de login utilizado pela API
# "/api/v3/auth/login" não possui barra final.

# instalar dependências e subir o app
poetry install --no-dev
poetry run streamlit run app/main.py
```


## Execução Rápida

- `poetry install --no-dev` – instala dependências
- `poetry run streamlit run app/main.py` – inicia o dashboard

## Boas práticas

Os nomes de arquivo em `app/pages/` devem usar apenas caracteres ASCII
(por exemplo, `1_home.py`, `2_os.py`). Cada página define seu título e ícone
com `st.set_page_config(page_icon="...")`. A sidebar é montada
automaticamente pelo Streamlit.

## Contribuindo

1. Crie uma branch a partir de `main`.
2. Commits descritivos e mensagens no imperativo.
3. Abra um Pull Request para revisao.

## Contato / Licenca

Projeto sob a [MIT License](LICENSE). Dúvidas abra uma issue.
<!-- Random comment for PR test -->
