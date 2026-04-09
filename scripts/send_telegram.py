#!/usr/bin/env python3
"""Send a Telegram bot message for DuoShe reminders."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib import error, parse, request


def default_config_path() -> Path:
    return Path(".duo-she") / "telegram.json"


def load_config(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def resolve_secret(
    cli_value: str | None,
    env_names: list[str],
    config: dict,
    config_key: str,
    label: str,
) -> str:
    if cli_value:
        return cli_value
    value = config.get(config_key)
    if value:
        return str(value)
    for name in env_names:
        value = os.getenv(name)
        if value:
            return value
    raise SystemExit(
        f"Missing {label}. Provide --{label.replace('_', '-')}, set one of: {', '.join(env_names)}, "
        f"or configure {default_config_path()}"
    )


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Telegram API error {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise SystemExit(f"Failed to reach Telegram API: {exc}") from exc

    result = json.loads(body)
    if not result.get("ok"):
        raise SystemExit(f"Telegram API rejected request: {body}")
    return result


def load_state(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a Telegram reminder via bot API.")
    parser.add_argument("--bot-token")
    parser.add_argument("--chat-id")
    parser.add_argument(
        "--config",
        default=str(default_config_path()),
        help="Path to Telegram config JSON. Defaults to .duo-she/telegram.json in the project.",
    )
    parser.add_argument("--text", help="Message text. If omitted, read from stdin.")
    parser.add_argument("--parse-mode", choices=["Markdown", "MarkdownV2", "HTML"])
    parser.add_argument("--disable-notification", action="store_true")
    parser.add_argument("--state-file", help="Optional JSON state file to update after sending.")
    parser.add_argument("--task-id", help="Optional task identifier stored in the state file.")
    parser.add_argument("--mission-id", help="Optional mission identifier stored in the state file.")
    parser.add_argument("--goal-snapshot", help="Optional goal summary stored in the state file.")
    parser.add_argument(
        "--reply-contract",
        help="Human-readable reply contract stored in the state file.",
    )
    parser.add_argument("--timezone", help="IANA timezone name for reminder evaluation.")
    parser.add_argument(
        "--quiet-hours",
        help="Quiet hours window in local time, for example 22:00-08:00.",
    )
    parser.add_argument(
        "--workday-end",
        help="Local workday end time, for example 22:00.",
    )
    parser.add_argument(
        "--deadline-minutes",
        type=int,
        help="Minutes after send time when the user is expected to reply.",
    )
    args = parser.parse_args()

    config = load_config(Path(args.config).expanduser())
    bot_token = resolve_secret(
        args.bot_token,
        ["TELEGRAM_BOT_TOKEN", "TG_BOT_TOKEN"],
        config,
        "bot_token",
        "bot_token",
    )
    chat_id = resolve_secret(
        args.chat_id,
        ["TELEGRAM_CHAT_ID", "TG_CHAT_ID"],
        config,
        "chat_id",
        "chat_id",
    )
    text = args.text if args.text is not None else sys.stdin.read().strip()
    if not text:
        raise SystemExit("Message text is empty. Provide --text or pipe text via stdin.")

    url = f"https://api.telegram.org/bot{parse.quote(bot_token, safe='')}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_notification": args.disable_notification,
    }
    if args.parse_mode:
        payload["parse_mode"] = args.parse_mode

    result = post_json(url, payload)
    message = result["result"]

    if args.state_file:
        state_path = Path(args.state_file)
        state = load_state(state_path)
        sent_at = int(time.time())
        quiet_hours = args.quiet_hours or state.get("quiet_hours") or "22:00-08:00"
        state.update(
            {
                "state_version": 2,
                "channel": "telegram",
                "status": "awaiting_reply",
                "awaiting_reply": True,
                "completed": False,
                "reply_status": "",
                "chat_id": str(chat_id),
                "last_prompt": text,
                "last_sent_at": sent_at,
                "last_sent_message_id": message.get("message_id"),
                "reminder_count": 0,
                "last_nudge_at": 0,
                "last_nudge_stage": "",
                "quiet_hours": quiet_hours,
                "workday_end": args.workday_end or state.get("workday_end") or quiet_hours.split("-", 1)[0],
                "reply_contract": args.reply_contract
                or state.get("reply_contract")
                or "done + evidence | partial + evidence | blocked + blocker | reschedule + new time",
            }
        )
        if args.timezone:
            state["timezone"] = args.timezone
        elif "timezone" not in state and os.getenv("TZ"):
            state["timezone"] = os.getenv("TZ")
        if args.deadline_minutes is not None:
            state["due_at"] = sent_at + int(args.deadline_minutes) * 60
        if args.task_id:
            state["task_id"] = args.task_id
        if args.mission_id:
            state["mission_id"] = args.mission_id
        if args.goal_snapshot:
            state["goal_snapshot"] = args.goal_snapshot
        save_state(state_path, state)

    summary = {
        "ok": True,
        "chat_id": str(chat_id),
        "message_id": message.get("message_id"),
        "date": message.get("date"),
    }
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
