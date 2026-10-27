"""Verify frozen Zenodo inputs; restore only missing files from registered URLs.

The checked-in WHO/benchmark text snapshots preserve a historical scrape. They
cannot be recreated by substituting today's web page; retrieve the Git snapshot.
"""
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def fetch(root=ROOT):
    source = root / "sources/snapshots/zenodo_22167512"
    manifest = json.loads((source / "inspection_download_manifest.json").read_text())
    verified = []
    for entry in manifest["files"]:
        path = source / entry["filename"]
        if path.parent != source:
            raise ValueError("Unsafe source filename")
        if path.exists():
            content = path.read_bytes()
        else:
            if not entry["url"].startswith("https://zenodo.org/api/records/22167512/files/"):
                raise ValueError("Unregistered download host/version")
            with urlopen(Request(entry["url"], headers={"User-Agent": "MeaslesWatch-BD-reproduction/0.1"}), timeout=60) as response:
                content = response.read(10_000_001)
            if len(content) > 10_000_000:
                raise ValueError("Unexpected source download size")
        if hashlib.sha256(content).hexdigest() != entry["sha256"] or len(content) != entry["bytes"]:
            raise ValueError(f"Frozen source changed: {path.name}; existing bytes will not be overwritten")
        if not path.exists():
            with path.open("xb") as handle:
                handle.write(content)
        verified.append(path.name)
    return verified


if __name__ == "__main__":
    print(json.dumps({"verified": fetch(), "downloaded_code_executed": False}, indent=2))
