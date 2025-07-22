#!/usr/bin/env bash
poetry install --with dev --no-root
poetry run streamlit run app/main.py "$@"
