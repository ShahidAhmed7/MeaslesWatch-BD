import argparse
from pathlib import Path

from measleswatch.report import build_report

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
print(build_report(Path(__file__).resolve().parents[1], args.output))
