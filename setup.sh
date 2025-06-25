#!/bin/bash
set -euo pipefail

echo "Instalando dependências..."
python -m pip install --upgrade pip
pip install pandas streamlit

echo "Configurando PYTHONPATH..."
export PYTHONPATH="$PYTHONPATH:$(pwd)"

echo "Setup concluído!"
