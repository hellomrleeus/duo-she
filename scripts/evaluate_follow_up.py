#!/usr/bin/env python3
"""Evaluate whether DuoShe should send another reminder."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

DEFAULT_OFFSETS = [0, 15, 45, 120]
DEFAULT_STAGES = ["gentle", "firm", "urgent", "reset"]


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def parse_offsets(raw: str) -> list[int]:
    values = [int(item.strip()) for item in raw.split(",") if item.strip()]
    if not values:
        raise SystemExit("Offsets cannot be empty.")
    return values


def decide(state: dict, now_ts: int, offsets: list[int], repeat_minutes: int) -> dict:
    if state.get("completed"):
        return {"action": "none", "reason": "completed"}
    if not state.get("awaiting_reply", False):
        return {"action": "none", "reason": "not-awaiting-reply"}
    due_at = state.get("due_at")
    if due_at is None:
        return {"action": "wait", "reason": "no-deadline"}

    due_at = int(due_at)
    elapsed_minutes = max(0, (now_ts - due_at) // 60)
    if now_ts < due_at:
        return {"action": "wait", "reason": "before-deadline", "wait_seconds": due_at - now_ts}

    reminder_count = int(state.get("reminder_count", 0))
    if reminder_count < len(offsets):
        next_offset = offsets[reminder_count]
        if elapsed_minutes >= next_offset:
            stage = DEFAULT_STAGES[min(reminder_count, len(DEFAULT_STAGES) - 1)]
            return {"action": "send", "stage": stage, "reminder_count": reminder_count}
        wait_seconds = (next_offset * 60) - (now_ts - due_at)
        return {"action": "wait", "reason": "waiting-next-offset", "wait_seconds": max(0, wait_seconds)}

    extra_count = reminder_count - len(offsets) + 1
    next_offset = offsets[-1] + extra_count * repeat_minutes
    if elapsed_minutes >= next_offset:
        return {"action": "send", "stage": "repeat", "reminder_count": reminder_count}
    wait_seconds = (next_offset * 60) - (now_ts - due_at)
    return {"action": "wait", "reason": "waiting-repeat-window", "wait_seconds": max(0, wait_seconds)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Decide whether to send another DuoShe reminder.")
    parser.add_argument("--state-file", required=True)
    parser.add_argument("--offsets", default="0,15,45,120")
    parser.add_argument("--repeat-minutes", type=int, default=60)
    parser.add_argument("--now", type=int)
    parser.add_argument("--mark-sent", action="store_true")
    args = parser.parse_args()

    state_path = Path(args.state_file)
    state = load_json(state_path)
    now_ts = args.now or int(time.time())
    decision = decide(state, now_ts, parse_offsets(args.offsets), args.repeat_minutes)

    if args.mark_sent and decision.get("action") == "send":
        state["reminder_count"] = int(state.get("reminder_count", 0)) + 1
        state["last_nudge_at"] = now_ts
        state["last_nudge_stage"] = decision["stage"]
        save_json(state_path, state)

    print(json.dumps(decision, ensure_ascii=False))


if __name__ == "__main__":
    main()
