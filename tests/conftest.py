import sys
from pathlib import Path

# Ensure app directory is on sys.path so modules can be imported without the
# `app.` prefix when running tests from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
