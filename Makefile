PORT ?= 8501

.PHONY: install lint format test run docker compose ci

install:
poetry install --with dev --no-root

lint:
poetry run ruff check .

format:
poetry run ruff format .

test:
poetry run pytest -q

run:
poetry run streamlit run app/main.py --server.port $(PORT)

docker:
docker build -t arkmeds-dashboard .

compose:
docker compose up --build

ci: lint test
