from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_METRICS_PATH = PROJECT_ROOT / "backend" / "training_logs" / "wardrobe_training_metrics.jsonl"


def resolve_path(path: str | Path) -> Path:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = PROJECT_ROOT / resolved
    return resolved.resolve()


def read_events(metrics_path: Path) -> list[dict]:
    if not metrics_path.exists():
        return []

    events: list[dict] = []
    with metrics_path.open("r", encoding="utf-8", errors="replace") as metrics_file:
        for line in metrics_file:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def format_number(value) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def print_progress(metrics_path: Path) -> None:
    events = read_events(metrics_path)
    if not events:
        print(f"[watch] waiting for metrics: {metrics_path}", flush=True)
        return

    start_event = next((event for event in events if event.get("event") == "start"), None)
    epoch_events = [event for event in events if event.get("event") == "epoch"]
    complete_event = next((event for event in reversed(events) if event.get("event") == "complete"), None)

    if start_event:
        print(
            f"[dataset] train={start_event.get('train_samples')} "
            f"val={start_event.get('val_samples')} "
            f"classes={len(start_event.get('class_names') or [])} "
            f"architecture={start_event.get('architecture')}",
            flush=True,
        )

    if epoch_events:
        last_epoch = epoch_events[-1]
        print(
            f"[epoch] {last_epoch.get('epoch')}/{last_epoch.get('epochs')} "
            f"train_loss={format_number(last_epoch.get('train_loss'))} "
            f"train_acc={format_number(last_epoch.get('train_accuracy'))} "
            f"val_loss={format_number(last_epoch.get('val_loss'))} "
            f"val_acc={format_number(last_epoch.get('val_accuracy'))} "
            f"best={format_number(last_epoch.get('best_val_accuracy'))} "
            f"seconds={last_epoch.get('seconds')}",
            flush=True,
        )
    else:
        print("[watch] training has started; no epoch is finished yet", flush=True)

    if complete_event:
        print(
            f"[complete] best_val_acc={format_number(complete_event.get('best_val_accuracy'))} "
            f"checkpoint={complete_event.get('checkpoint_path')}",
            flush=True,
        )


def parse_args():
    parser = argparse.ArgumentParser(description="Watch Project Wardrobe classifier training progress.")
    parser.add_argument("--metrics-path", default=str(DEFAULT_METRICS_PATH))
    parser.add_argument("--interval", type=float, default=10.0)
    parser.add_argument("--once", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    metrics_path = resolve_path(args.metrics_path)
    if args.once:
        print_progress(metrics_path)
        return

    print(f"[watch] metrics: {metrics_path}", flush=True)
    while True:
        print_progress(metrics_path)
        time.sleep(max(args.interval, 1.0))


if __name__ == "__main__":
    main()
