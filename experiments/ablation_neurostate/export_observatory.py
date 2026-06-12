from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


def read_events(input_dirs: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for input_dir in input_dirs:
        events_path = input_dir / "events.jsonl"
        if not events_path.exists():
            raise FileNotFoundError(f"Missing {events_path}")
        with events_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows


def to_timeline_rows(rows: list[dict[str, Any]], source_label: str) -> list[dict[str, Any]]:
    base_ts = datetime(2026, 6, 12, tzinfo=timezone.utc)
    timeline = []
    for idx, row in enumerate(sorted(rows, key=lambda r: (r["trial_id"], r["condition"], r["scenario"])), start=1):
        timeline.append(
            {
                "sequence": idx,
                "timestamp_utc": (base_ts + timedelta(seconds=idx)).isoformat().replace("+00:00", "Z"),
                "source": source_label,
                "event_type": "attack_result" if row.get("attack") else "normal_result",
                "condition": row["condition"],
                "scenario": row["scenario"],
                "scenario_kind": row.get("scenario_kind", ""),
                "trial_id": row["trial_id"],
                "attack": row.get("attack", False),
                "attack_success": row.get("attack_success", False),
                "detected": row.get("detected", False),
                "detected_turn": row.get("detected_turn"),
                "blocked": row.get("blocked", False),
                "turns_executed": row.get("turns_executed", 0),
                "mean_turn_ms": row.get("mean_turn_ms", 0.0),
                "final_state": {
                    "calm": row.get("final_calm"),
                    "corruption": row.get("final_corruption"),
                },
                "gate": {
                    "status": row.get("engine_gate_status", ""),
                    "reason": row.get("engine_gate_reason", ""),
                },
                "tags": [
                    row["condition"].lower(),
                    row.get("scenario_kind", ""),
                    "attack" if row.get("attack") else "normal",
                ],
            }
        )
    return timeline


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_condition = Counter()
    attack_success = Counter()
    attack_count = Counter()
    normal_count = Counter()
    blocked_count = Counter()

    for row in rows:
        condition = row["condition"]
        by_condition[condition] += 1
        if row.get("attack"):
            attack_count[condition] += 1
            if row.get("attack_success"):
                attack_success[condition] += 1
        else:
            normal_count[condition] += 1
            if row.get("blocked"):
                blocked_count[condition] += 1

    return {
        "total_events": len(rows),
        "conditions": sorted(by_condition),
        "by_condition": {
            cond: {
                "rows": by_condition[cond],
                "attack_rows": attack_count[cond],
                "attack_success_rows": attack_success[cond],
                "normal_rows": normal_count[cond],
                "blocked_normal_rows": blocked_count[cond],
            }
            for cond in sorted(by_condition)
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Export CPOS ablation events to an observatory-style timeline.")
    parser.add_argument("input_dirs", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-label", default="cpos.ablation_neurostate")
    args = parser.parse_args()

    rows = read_events(args.input_dirs)
    timeline_rows = to_timeline_rows(rows, args.source_label)
    summary = summarize(rows)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    timeline_path = args.output_dir / "observatory_timeline.jsonl"
    with timeline_path.open("w", encoding="utf-8") as f:
        for row in timeline_rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    summary_path = args.output_dir / "observatory_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, sort_keys=True)

    markdown_path = args.output_dir / "observatory_summary.md"
    with markdown_path.open("w", newline="", encoding="utf-8") as f:
        f.write("# NeuroState Observatory Export\n\n")
        f.write(f"- Total events: {summary['total_events']}\n")
        f.write(f"- Conditions: {', '.join(summary['conditions'])}\n\n")
        f.write("| Condition | Rows | Attack rows | Attack success rows | Normal rows | Blocked normal rows |\n")
        f.write("| --- | ---: | ---: | ---: | ---: | ---: |\n")
        for cond, data in summary["by_condition"].items():
            f.write(
                f"| {cond} | {data['rows']} | {data['attack_rows']} | {data['attack_success_rows']} | "
                f"{data['normal_rows']} | {data['blocked_normal_rows']} |\n"
            )

    print(f"Wrote {timeline_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
