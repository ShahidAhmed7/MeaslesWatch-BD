import json

import pytest

from measleswatch.report import build_report


def test_report_refuses_to_invent_results_for_an_incomplete_experiment(tmp_path):
    run = tmp_path / "results/research-001"
    run.mkdir(parents=True)
    (run / "run_manifest.json").write_text(json.dumps({"status": "running", "completed_jobs": 10}))
    output = tmp_path / "reports/draft.md"
    with pytest.raises(ValueError, match="complete measured"):
        build_report(tmp_path, output)
    assert not output.exists()
