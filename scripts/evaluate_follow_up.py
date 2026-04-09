#!/usr/bin/env python3
"""Evaluate whether DuoShe should send another reminder."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_OFFSETS = [0, 15, 45, 120]
DEFAULT_STAGES = ["gentle", "firm", "urgent", "reset"]
DEFAULT_TIMEZONE = "UTC"
DEFAULT_QUIET_HOURS = "22:00-08:00"


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


def parse_clock(raw: str) -> tuple[int, int]:
    try:
        hour_raw, minute_raw = raw.split(":", 1)
        hour = int(hour_raw)
        minute = int(minute_raw)
    except (ValueError, AttributeError) as exc:
        raise SystemExit(f"Invalid clock value: {raw}") from exc
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise SystemExit(f"Invalid clock value: {raw}")
    return hour, minute


def parse_quiet_hours(raw: str) -> tuple[tuple[int, int], tuple[int, int]]:
    try:
        start_raw, end_raw = raw.split("-", 1)
    except ValueError as exc:
        raise SystemExit(f"Invalid quiet hours window: {raw}") from exc
    return parse_clock(start_raw), parse_clock(end_raw)


def resolve_timezone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise SystemExit(f"Unknown timezone: {name}") from exc


def clock_minutes(clock: tuple[int, int]) -> int:
    hour, minute = clock
    return hour * 60 + minute


def local_minutes(moment: datetime) -> int:
    return moment.hour * 60 + moment.minute


def replace_clock(moment: datetime, clock: tuple[int, int]) -> datetime:
    return moment.replace(hour=clock[0], minute=clock[1], second=0, microsecond=0)


def is_in_quiet_hours(moment: datetime, quiet_hours: tuple[tuple[int, int], tuple[int, int]]) -> bool:
    start, end = quiet_hours
    start_minutes = clock_minutes(start)
    end_minutes = clock_minutes(end)
    current = local_minutes(moment)
    if start_minutes == end_minutes:
        return False
    if start_minutes < end_minutes:
        return start_minutes <= current < end_minutes
    return current >= start_minutes or current < end_minutes


def next_quiet_end(moment: datetime, quiet_hours: tuple[tuple[int, int], tuple[int, int]]) -> datetime:
    start, end = quiet_hours
    start_minutes = clock_minutes(start)
    end_minutes = clock_minutes(end)
    current = local_minutes(moment)
    end_today = replace_clock(moment, end)

    if start_minutes == end_minutes:
        return moment
    if start_minutes < end_minutes:
        if current < end_minutes:
            return end_today
        return end_today + timedelta(days=1)
    if current >= start_minutes:
        return end_today + timedelta(days=1)
    return end_today


def next_active_window_start(
    moment: datetime,
    quiet_hours: tuple[tuple[int, int], tuple[int, int]],
    workday_end: tuple[int, int],
) -> datetime:
    if is_in_quiet_hours(moment, quiet_hours):
        return next_quiet_end(moment, quiet_hours)

    workday_end_at = replace_clock(moment, workday_end)
    if moment >= workday_end_at:
        next_day = moment + timedelta(days=1)
        return replace_clock(next_day, quiet_hours[1])

    return moment


def decide(state: dict, now_ts: int, offsets: list[int], repeat_minutes: int) -> dict:
    if state.get("completed"):
        return {"action": "none", "reason": "completed"}
    if not state.get("awaiting_reply", False):
        return {"action": "none", "reason": "not-awaiting-reply"}

    due_at = state.get("due_at")
    if due_at is None:
        return {"action": "wait", "reason": "no-deadline"}

    timezone_name = state.get("timezone") or DEFAULT_TIMEZONE
    quiet_hours_raw = state.get("quiet_hours") or DEFAULT_QUIET_HOURS
    workday_end_raw = state.get("workday_end") or quiet_hours_raw.split("-", 1)[0]
    zone = resolve_timezone(timezone_name)
    quiet_hours = parse_quiet_hours(quiet_hours_raw)
    workday_end = parse_clock(workday_end_raw)

    due_at = int(due_at)
    now_local = datetime.fromtimestamp(now_ts, zone)
    due_local = datetime.fromtimestamp(due_at, zone)
    elapsed_minutes = max(0, (now_ts - due_at) // 60)

    if now_ts < due_at:
        return {"action": "wait", "reason": "before-deadline", "wait_seconds": due_at - now_ts}

    reminder_count = int(state.get("reminder_count", 0))
    if reminder_count < len(offsets):
        next_offset = offsets[reminder_count]
        if elapsed_minutes >= next_offset:
            stage = DEFAULT_STAGES[min(reminder_count, len(DEFAULT_STAGES) - 1)]
            decision = {"action": "send", "stage": stage, "reminder_count": reminder_count}
        else:
            wait_seconds = (next_offset * 60) - (now_ts - due_at)
            return {"action": "wait", "reason": "waiting-next-offset", "wait_seconds": max(0, wait_seconds)}
    else:
        extra_count = reminder_count - len(offsets) + 1
        next_offset = offsets[-1] + extra_count * repeat_minutes
        if elapsed_minutes >= next_offset:
            decision = {"action": "send", "stage": "repeat", "reminder_count": reminder_count}
        else:
            wait_seconds = (next_offset * 60) - (now_ts - due_at)
            return {"action": "wait", "reason": "waiting-repeat-window", "wait_seconds": max(0, wait_seconds)}

    resume_at = next_active_window_start(now_local, quiet_hours, workday_end)
    if resume_at > now_local:
        return {
            "action": "wait",
            "reason": "outside-active-window",
            "wait_seconds": int((resume_at - now_local).total_seconds()),
            "resume_at": int(resume_at.timestamp()),
            "deferred_stage": "reset" if now_local.date() > due_local.date() else decision["stage"],
        }

    if now_local.date() > due_local.date():
        decision["stage"] = "reset"
        decision["reason"] = "rolled-over-to-next-day"

    decision["timezone"] = timezone_name
    return decision


def main() -> None:
    parser = argparse.ArgumentParser(description="Decide whether to send another DuoShe reminder.")
    parser.add_argument("--state-file", required=True)
    parser.add_argument("--offsets", default="0,15,45,120")
    parser.add_argument("--repeat-minutes", type=int, default=60)
    parser.add_argument("--now", type=int)
    parser.add_argument("--timezone", help="Override timezone for this evaluation run.")
    parser.add_argument("--quiet-hours", help="Override quiet hours, for example 22:00-08:00.")
    parser.add_argument("--workday-end", help="Override local workday end, for example 22:00.")
    parser.add_argument("--mark-sent", action="store_true")
    args = parser.parse_args()

    state_path = Path(args.state_file)
    state = load_json(state_path)
    if args.timezone:
        state["timezone"] = args.timezone
    if args.quiet_hours:
        state["quiet_hours"] = args.quiet_hours
    if args.workday_end:
        state["workday_end"] = args.workday_end

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
