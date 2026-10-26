"""Explicit, bounded WHO API reconciliation; never called during dashboard use."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import urlopen

from measleswatch.ingest import sha256, write_json

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://xmart-api-public.who.int/WIISE/AD_COVERAGES"


def fetch(params):
    url = BASE + "?" + urlencode(params)
    pages, records, visited = [], [], set()
    expected = None
    while url:
        if url in visited or len(visited) >= 10 or urlparse(url).netloc != urlparse(BASE).netloc:
            raise ValueError("Unexpected pagination or source host")
        visited.add(url)
        with urlopen(url, timeout=40) as response:
            raw = response.read(200_001)
        if len(raw) > 200_000:
            raise ValueError("Bounded source response exceeded expected size")
        data = json.loads(raw)
        if expected is None:
            expected = int(data["@odata.count"])
        pages.append({"url": url, "raw": raw})
        records.extend(data["value"])
        url = data.get("@odata.nextLink")
    if len(records) != expected:
        raise ValueError("OData record count did not reconcile; possible truncation")
    return pages, records


def check(output):
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    common = "COUNTRY eq 'BGD' and (YEAR eq 2024 or YEAR eq 2025) and (VACCINECODE eq 'MCV1' or VACCINECODE eq 'MCV2')"
    selection = "COUNTRY,YEAR,VACCINECODE,COVERAGE_CATEGORY,TIMELYDOSES,AGEGROUP,PERCENTAGE,REVISION_YEAR,TARGETNUMBER,DOSES,TARGETDEFINITION_CMT"
    ap, admin = fetch({"$filter": common + " and COVERAGE_CATEGORY eq 'ADMIN' and TIMELYDOSES eq 'ON_TIME' and AGEGROUP eq 'NOT_COLLECTED'", "$select": selection, "$count": "true"})
    op, other = fetch({"$filter": common + " and (COVERAGE_CATEGORY eq 'OFFICIAL' or COVERAGE_CATEGORY eq 'WUENIC')", "$select": selection, "$count": "true"})
    selected = admin + [r for r in other if r["COVERAGE_CATEGORY"] == "OFFICIAL" or r["REVISION_YEAR"] == 2025]
    index = {(r["YEAR"], r["VACCINECODE"], r["COVERAGE_CATEGORY"].lower()): r for r in selected}
    if len(index) != 12 or len(selected) != 12:
        raise ValueError("Expected exactly one row per year, antigen and selected source")
    canonical = json.loads((ROOT / "data/processed/phase1-r2/coverage_annual.json").read_text())
    comparisons = []
    for row in canonical:
        key = (row["year"], row["antigen"], row["coverage_source"])
        if key not in index:
            continue
        external = index[key]
        fields = [("reported_pct", "PERCENTAGE", .005)]
        if key[2] == "admin":
            fields += [("admin_doses", "DOSES", 0), ("admin_target", "TARGETNUMBER", 0)]
        for local, remote, tolerance in fields:
            a, b = row[local], external[remote]
            comparisons.append({"year": key[0], "antigen": key[1], "source": key[2], "field": local,
                "frozen_value": a, "current_value": b, "absolute_tolerance": tolerance,
                "agrees": a is not None and b is not None and abs(a - b) <= tolerance,
                "frozen_source_row": row["source_row"]})
    if len(comparisons) != 20:
        raise ValueError("Incomplete source comparisons")
    output.mkdir(parents=True)
    pages = ap + op
    requests = []
    for i, page in enumerate(pages, 1):
        path = output / f"response-{i}.json"
        path.write_bytes(page["raw"])
        requests.append({"url": page["url"], "file": path.name, "sha256": sha256(path)})
    write_json(output / "reconciliation.json", comparisons)
    write_json(output / "selected_records.json", selected)
    result = {"status": "reconciled" if all(r["agrees"] for r in comparisons) else "source_revision_or_discrepancy",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "requests": requests,
        "selected_records": len(selected), "comparisons": len(comparisons),
        "WUENIC_revision_year": 2025, "selection": "ADMIN: ON_TIME + NOT_COLLECTED; OFFICIAL; WUENIC 2025 revision",
        "frozen_data_replaced": False, "scope": "Coverage records only; monthly surveillance retains attributed frozen August extract",
        "artifact_sha256": {p.name: sha256(p) for p in output.glob("*.json")}, "script_sha256": sha256(Path(__file__))}
    write_json(output / "manifest.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.output), indent=2))
