#!/usr/bin/env bash
set -euo pipefail

echo "Instalando dependências..."
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "Configurando PYTHONPATH..."
export PYTHONPATH="$PYTHONPATH:$(pwd)"

echo "Setup concluído!"
