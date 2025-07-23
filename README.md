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
- Docker
- [Poetry](https://python-poetry.org/docs/#installation)

## Quick Start

```bash
# configure variáveis locais
cp .env.example .env
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# instalar dependências e subir o app (Linux/macOS)
make install && make run

# no Windows (cmd ou PowerShell via Batch)
./make.bat install
./make.bat run PORT=8501
# ou em PowerShell puro
./make.ps1 -Target install
./make.ps1 -Target run -Port 8501
# se bloquear scripts, use
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```


## Scripts Uteis

- `make install` – instala as dependências
- `make lint` – ruff lint
- `make format` – ruff format
- `make test` – pytest
- `make run` – inicia o Streamlit em localhost:8501
- `make docker` – build da imagem Docker
- `make compose` – docker compose up --build
- `make ci` – executa lint e testes

## Problemas comuns

Em algumas versões antigas do Windows a renderização de emojis pode disparar
`UnicodeEncodeError` ao iniciar o Streamlit. O dashboard tenta detectar esse
cenário e remove os ícones automaticamente. Se preferir desativar os emojis em
qualquer plataforma defina a variável de ambiente `ALLOW_EMOJI=0` (no
PowerShell: `setx ALLOW_EMOJI 0`).
Defina `setx ALLOW_EMOJI 0` para forçar remoção de emoji em qualquer SO.
Se ainda ver erro `UnicodeEncodeError`, defina `setx ALLOW_EMOJI 0` e reinicie terminal.

## Contribuindo

1. Crie uma branch a partir de `main`.
2. Commits descritivos e mensagens no imperativo.
3. Abra um Pull Request para revisao.

## Contato / Licenca

Projeto sob a [MIT License](LICENSE). Dúvidas abra uma issue.
