@echo off
setlocal

if "%1"=="install" (
    poetry install --with dev --no-root
) else if "%1"=="run" (
    if "%PORT%"=="" set PORT=8501
    poetry run streamlit run app/main.py --server.port %PORT%
) else if "%1"=="lint" (
    poetry run ruff check .
) else if "%1"=="format" (
    poetry run ruff format .
) else if "%1"=="test" (
    poetry run pytest -q
) else if "%1"=="docker" (
    docker build -t arkmeds-dashboard .
) else if "%1"=="compose" (
    docker compose up --build
) else if "%1"=="ci" (
    call %0 lint
    call %0 test
) else (
    echo Targets: install run lint format test docker compose ci
    exit /b 1
)

endlocal
