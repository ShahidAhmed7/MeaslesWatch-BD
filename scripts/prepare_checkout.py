"""Restore private-answer file permissions after a Git checkout; no inference."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "benchmark/private").rglob("*"):
    if path.is_file():
        path.chmod(0o600)
print("Private scorer-only answer files set to owner read/write. No model run started.")
