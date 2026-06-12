from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path
from typing import Any

from run_llm_ablation import summarize


def read_events(input_dirs: list[Path]) -> list[dict[str, Any]]:
    rows = []
    for input_dir in input_dirs:
        events_path = input_dir / "events.jsonl"
        if not events_path.exists():
            raise FileNotFoundError(f"Missing {events_path}")
        with events_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge split LLM ablation runs.")
    parser.add_argument("input_dirs", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    rows = read_events(args.input_dirs)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    events_path = args.output_dir / "events.jsonl"
    with events_path.open("w", encoding="utf-8") as f:
        for row in sorted(rows, key=lambda r: (r["trial_id"], r["condition"], r["scenario"])):
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    summary_rows = summarize(rows)
    summary_path = args.output_dir / "summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"Merged {len(rows)} events")
    print(f"Wrote {events_path}")
    print(f"Wrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
