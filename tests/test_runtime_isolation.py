"""Exercise runtime operations with OS-audited denial of private answer access."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_model_inputs_and_verification_work_when_private_answers_are_inaccessible():
    script = r'''
import json, sys
from pathlib import Path
root = Path.cwd()
private = (root / "benchmark/private").resolve()
def guard(event, args):
    if event == "open" and isinstance(args[0], (str, bytes)):
        path = Path(args[0]).resolve()
        if path.is_relative_to(private):
            raise PermissionError("Private scorer material denied")
sys.addaudithook(guard)
try:
    (private / "external-v1/gold.json").read_text()
except PermissionError:
    pass
else:
    raise AssertionError("Audit guard is inactive")
from measleswatch.benchmark_runtime import load_public, build_messages, verify_external
for split in ("development", "test"):
    store, items = load_public(root, split)
    for item in items:
        for condition in ("A", "B"):
            payload = json.dumps(build_messages(store, item, condition))
            assert not any(x in payload for x in ("expected_status", "independent_operation", "absolute_tolerance", "scope_overrides"))
        assert verify_external(store, item, {})["claims"] == []
print("36 runtime items exercised without private access")
'''
    result = subprocess.run([sys.executable, "-c", script], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert "36 runtime items" in result.stdout


def test_deployed_source_package_contains_only_python_code_and_no_gold():
    # add_local_python_source uploads this package directory, not the project root.
    source = ROOT / "src/measleswatch"
    files = [p for p in source.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    assert files and all(p.suffix == ".py" and not p.is_symlink() for p in files)
    import inspect
    import modal_app
    import modal_service
    settings = inspect.getsource(modal_app).split("@app.function")[0]
    assert '.add_local_python_source("measleswatch")' in settings
    assert ".add_local_dir" not in settings
    assert "modal.Secret" not in inspect.getsource(modal_service)
    assert modal_service.app._local_state.web_endpoints == []
    assert modal_service.app._local_state.local_entrypoints == {}
