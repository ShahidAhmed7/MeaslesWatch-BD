import argparse
import json
from pathlib import Path

from measleswatch.ingest import ValidationError, run_ingestion


def main():
    parser = argparse.ArgumentParser(prog="measleswatch")
    subcommands = parser.add_subparsers(dest="command", required=True)
    ingest = subcommands.add_parser("ingest", help="Verify frozen inputs and build canonical tables")
    ingest.add_argument("--project-root", type=Path, default=Path.cwd())
    ingest.add_argument("--output", type=Path, required=True, help="New run directory; never overwritten")
    for name in ("audit", "describe", "evaluate", "figures", "reproduce", "infer"):
        command = subcommands.add_parser(name)
        command.add_argument("--project-root", type=Path, default=Path.cwd())
        command.add_argument("--output", type=Path, required=True)
        if name == "infer":
            command.add_argument("--resume", action="store_true")
            command.add_argument("--brief-selection", type=Path)
    score = subcommands.add_parser("score")
    score.add_argument("--project-root", type=Path, default=Path.cwd())
    score.add_argument("--run", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "ingest":
            manifest = run_ingestion(args.project_root, args.output)
        elif args.command == "audit":
            from measleswatch.audit import build_audit
            manifest = build_audit(args.project_root, args.output)
        elif args.command == "describe":
            from measleswatch.describe import run_description
            manifest = run_description(args.project_root / "data/processed/phase1-r2", args.output,
                args.project_root / ".devin/study.toml", args.project_root / ".devin/analysis_protocol.toml")
        elif args.command == "evaluate":
            from measleswatch.evaluate import run_evaluation
            manifest = run_evaluation(args.project_root, args.output)
        elif args.command == "figures":
            from measleswatch.figures import generate
            manifest = {"figures": generate(args.project_root, args.output)}
        elif args.command == "reproduce":
            from measleswatch.pipeline import reproduce
            manifest = reproduce(args.project_root, args.output)
        elif args.command == "score":
            from measleswatch.score import score_run
            manifest = {"scorecard": score_run(args.project_root, args.run, args.output)}
        else:
            from measleswatch.inference_run import run
            selection = json.loads(args.brief_selection.read_text()) if args.brief_selection else None
            manifest = run(args.project_root, args.output, selection, args.resume)
    except (ValidationError, FileExistsError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps({"status": "validated" if args.command == "ingest" else "completed", "result": manifest,
                      "row_counts": manifest.get("row_counts"), "output": str(args.output.resolve())}, indent=2))


if __name__ == "__main__":
    main()
