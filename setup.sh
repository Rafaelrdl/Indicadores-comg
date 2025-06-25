#!/usr/bin/env bash
set -euo pipefail

echo "Instalando dependências..."
python -m pip install --upgrade pip
pip install pandas streamlit

echo "Setup concluído!"
