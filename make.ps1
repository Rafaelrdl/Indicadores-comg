Param([string]$Target="help", [int]$Port=8501)
function Run($cmd){ Write-Host "> $cmd"; iex $cmd }
switch ($Target) {
    "install" { Run "poetry install --with dev --no-root && poetry run pip install -e ." }
    "run" { Run "poetry run streamlit run app/main.py --server.port $Port" }
    "lint" { Run "poetry run ruff check ." }
    "format" { Run "poetry run ruff format ." }
    "test" { Run "poetry run pytest -q" }
    "docker" { Run "docker build -t arkmeds-dashboard ." }
    "ci" { Run "$PSCommandPath lint"; Run "$PSCommandPath test" }
    default { Write-Host "Targets: install run lint format test docker ci" }
}
