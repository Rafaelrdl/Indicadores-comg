param(
    [switch]$Install
)

if ($Install) {
    poetry install --with dev --no-root
}

poetry run streamlit run app/main.py @Args
