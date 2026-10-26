import argparse
import json
import os
import platform
import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal
from importlib.metadata import version
from pathlib import Path

from measleswatch.ingest import load_config, sha256, write_json


def modal_json(project_root, profile, *arguments):
    command = [str(project_root / ".venv/bin/modal"), *arguments, "--json", "--profile", profile]
    completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=45)
    return json.loads(completed.stdout)


def reserve_pilot(ledger, config, run_id, rates):
    limits = config["modal"]
    if (limits["gpu"] != "L4" or limits["max_containers"] != 1
            or limits["min_containers"] != 0 or limits["timeout_seconds"] > 900):
        raise ValueError("Pilot pricing recipe supports only one bounded, scale-to-zero L4 container")
    estimate = Decimal(str(limits["pilot_estimate_limit_usd"]))
    rate = (Decimal(rates["gpu_hour_cost_l4"])
            + Decimal(rates["cpu_hour_cost"]) * Decimal(str(limits["cpu"]))
            + Decimal(rates["mem_gib_hour_cost"]) * Decimal(limits["memory_mib"]) / 1024)
    wall_seconds = 1800
    reserved_seconds = wall_seconds + limits["scaledown_window_seconds"]
    resource_estimate = rate * Decimal(reserved_seconds) / 3600
    overhead_reserve = Decimal("1.25")
    if resource_estimate + overhead_reserve > estimate:
        raise ValueError("Current rates exceed the conservative pilot reservation")
    entries = ledger["entries"]
    if any(entry["run_id"] == run_id for entry in entries):
        raise ValueError("Run ID already reserved; refusing automatic retry")
    if sum(Decimal(entry["reserved_usd"]) for entry in entries) + estimate > min(
        Decimal(str(limits["working_limit_usd"])),
        Decimal(str(limits["absolute_authorization_usd"])),
    ):
        raise ValueError("Cumulative conservative reservations exceed the project working budget")
    if sum(entry["requested_generations"] for entry in entries) + 1 > limits["hard_generation_limit"]:
        raise ValueError("Generation-count limit exceeded")
    if sum(entry["reserved_container_seconds"] for entry in entries) + reserved_seconds > (
        limits["max_gpu_container_hours"] * 3600
    ):
        raise ValueError("Cumulative conservative GPU lifetime reservation exceeded")
    entry = {
        "run_id": run_id, "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "reserved", "reserved_usd": str(estimate),
        "requested_generations": 1, "reserved_container_seconds": reserved_seconds,
        "client_wall_timeout_seconds": wall_seconds,
        "requested_resource_rate_usd_per_hour": str(rate),
        "requested_resource_estimate_usd": str(resource_estimate),
        "image_build_storage_accounting_headroom_usd": str(overhead_reserve),
        "estimate_is_provider_billing_cap": False,
        "billing_control_evidence": "user_confirmed_after_request_for_workspace_usage_and_zero_out_of_pocket_limits",
        "provider_dashboard_independently_inspected": False,
        "measured_app_cost_usd": None,
    }
    entries.append(entry)
    return entry


def run(project_root, output_dir, preflight_dir, workspace, budget_confirmed):
    project_root = Path(project_root).resolve()
    output_dir, preflight_dir = Path(output_dir).resolve(), Path(preflight_dir).resolve()
    config_path = project_root / ".devin/study.toml"
    config = load_config(config_path)
    if not budget_confirmed or workspace != config["modal"]["profile"]:
        raise ValueError("Explicit budget confirmation and the configured workspace are required")
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite a pilot attempt: {output_dir}")
    token_info = (preflight_dir / "token-info.stdout").read_text()
    if f"Workspace: {workspace} (" not in token_info:
        raise ValueError("Authenticated preflight workspace does not match")
    rates = json.loads((preflight_dir / "billing-rates.stdout").read_text())
    os.environ["MODAL_PROFILE"] = workspace
    if modal_json(project_root, workspace, "app", "list"):
        raise ValueError("App list is not empty; inspect it before creating a pilot application")
    before = modal_json(project_root, workspace, "billing", "summary")
    ledger_path = project_root / ".devin/modal_ledger.json"
    lock_path = project_root / ".devin/modal_run.lock"
    with lock_path.open("x") as lock:
        lock.write(output_dir.name)
    entry = None
    started = time.monotonic()
    try:
        ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {
            "schema_version": "1.0.0", "workspace": workspace, "entries": [],
        }
        if ledger["workspace"] != workspace:
            raise ValueError("Ledger belongs to another workspace")
        entry = reserve_pilot(ledger, config, output_dir.name, rates)
        output_dir.mkdir(parents=True)
        write_json(output_dir / "billing_before.json", before)
        write_json(output_dir / "rates.json", rates)
        write_json(ledger_path, ledger)
        sys.path.insert(0, str(project_root))
        import modal
        import modal_app

        manifest = {
            "run_id": output_dir.name, "workspace": workspace, "environment": "main",
            "study_config_sha256": sha256(config_path),
            "modal_app_sha256": sha256(project_root / "modal_app.py"),
            "runner_sha256": sha256(Path(__file__)),
            "python": platform.python_version(), "platform": platform.platform(),
            "modal_sdk_version": version("modal"),
            "image_packages": modal_app.GPU_IMAGE_PACKAGES,
            "model_id": config["modal"]["model_id"],
            "model_revision": config["modal"]["model_revision"],
            "request": [
                {"role": "system", "content": config["pilot"]["system_message"]},
                {"role": "user", "content": config["pilot"]["user_message"]},
            ],
            "purpose": "Connectivity and structured-output pilot, not a benchmark item",
            "status": "starting", "budget_reservation": entry,
            "preflight_sha256": {
                name: sha256(preflight_dir / name)
                for name in ("token-info.stdout", "billing-rates.stdout", "app-list.stdout")
            },
        }
        write_json(output_dir / "run_manifest.json", manifest)

        def timed_out(signum, frame):
            raise TimeoutError("Pilot client exceeded its 1800-second wall limit")

        previous_alarm_handler = signal.signal(signal.SIGALRM, timed_out)
        signal.alarm(entry["client_wall_timeout_seconds"])
        try:
            with modal.enable_output():
                with modal_app.app.run(name=output_dir.name, environment_name="main"):
                    manifest["app_id"] = modal_app.app.app_id
                    entry["app_id"] = manifest["app_id"]
                    manifest["status"] = "running"
                    write_json(output_dir / "run_manifest.json", manifest)
                    write_json(ledger_path, ledger)
                    response = modal_app.pilot.remote(manifest["request"])
                    write_json(output_dir / "response.json", response)
                    parsed = modal_app.parse_pilot_response(response["text"])
                    if response["truncated"]:
                        raise ValueError("Pilot response did not terminate with an EOS token")
                    write_json(output_dir / "parsed_response.json", parsed)
            manifest["status"] = "succeeded"
            entry["status"] = "succeeded"
        except BaseException as error:
            manifest["status"] = "failed"
            entry["status"] = "failed"
            message = re.sub(r"\b(?:ak|as)-[A-Za-z0-9_-]+", "[REDACTED]", str(error))
            manifest["error"] = {"type": type(error).__name__, "message": message}
            raise
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, previous_alarm_handler)
            entry["client_wall_seconds"] = time.monotonic() - started
            entry["ended_at_utc"] = datetime.now(timezone.utc).isoformat()
            try:
                after = modal_json(project_root, workspace, "billing", "summary")
                write_json(output_dir / "billing_after.json", after)
                entry["workspace_metered_delta_usd"] = str(
                    Decimal(after["metered_cost"]) - Decimal(before["metered_cost"]))
                entry["workspace_delta_caveat"] = (
                    "May lag and include unrelated activity; not an app-attributed charge. "
                    "Conservative reservation is retained rather than released.")
                apps = modal_json(project_root, workspace, "app", "list")
                write_json(output_dir / "apps_after.json", apps)
            except Exception as error:
                manifest["accounting_status"] = f"unavailable: {type(error).__name__}"
            manifest["finished_at_utc"] = entry["ended_at_utc"]
            write_json(output_dir / "run_manifest.json", manifest)
            write_json(ledger_path, ledger)
        return manifest
    finally:
        lock_path.unlink()


def main():
    parser = argparse.ArgumentParser(description="Explicit single-attempt private Modal pilot")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--budget-confirmed", action="store_true")
    args = parser.parse_args()
    manifest = run(args.project_root, args.output, args.preflight, args.workspace, args.budget_confirmed)
    print(json.dumps({"status": manifest["status"], "app_id": manifest.get("app_id"),
                      "output": str(args.output.resolve())}, indent=2))


if __name__ == "__main__":
    main()
