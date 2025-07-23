@echo off
setlocal EnableDelayedExpansion
REM Porta padrão pode ser sobreposta com PORT=xxxx
if "%PORT%"=="" set PORT=8501
REM ---- TARGETS -------------------------------------------------
if "%1"=="install" (poetry install --with dev --no-root && poetry run pip install -e . & goto :eof)
if "%1"=="run" (poetry run streamlit run app/main.py --server.port !PORT! & goto :eof)
if "%1"=="lint" (poetry run ruff check . & goto :eof)
if "%1"=="format" (poetry run ruff format . & goto :eof)
if "%1"=="test" (poetry run pytest -q & goto :eof)
if "%1"=="docker" (docker build -t arkmeds-dashboard . & goto :eof)
if "%1"=="ci" (call %0 lint & call %0 test & goto :eof)
REM Help
echo Targets: install run lint format test docker ci
endlocal
