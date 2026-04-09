#!/usr/bin/env python3
"""Send an email reminder for DuoShe via SMTP."""

from __future__ import annotations

import argparse
import json
import os
import smtplib
import sys
import time
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from pathlib import Path


def default_config_path() -> Path:
    return Path(".duo-she") / "email.json"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def resolve_value(cli_value: str | int | None, config: dict, key: str, label: str) -> str:
    if cli_value is not None and str(cli_value).strip():
        return str(cli_value).strip()
    value = config.get(key)
    if value is not None and str(value).strip():
        return str(value).strip()
    raise SystemExit(f"Missing {label}. Provide it explicitly or configure {default_config_path()}")


def open_smtp(config: dict) -> smtplib.SMTP:
    host = resolve_value(None, config, "smtp_host", "smtp_host")
    port = int(resolve_value(None, config, "smtp_port", "smtp_port"))
    security = resolve_value(None, config, "smtp_security", "smtp_security").lower()

    if security == "ssl":
        server: smtplib.SMTP = smtplib.SMTP_SSL(host, port, timeout=20)
    else:
        server = smtplib.SMTP(host, port, timeout=20)
        if security == "starttls":
            server.starttls()

    username = resolve_value(None, config, "username", "username")
    password = resolve_value(None, config, "password", "password")
    server.login(username, password)
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="Send an email reminder via SMTP.")
    parser.add_argument("--config", default=str(default_config_path()))
    parser.add_argument("--subject", required=True)
    parser.add_argument("--text", help="Plain text email body. If omitted, read from stdin.")
    parser.add_argument("--to-email")
    parser.add_argument("--from-email")
    parser.add_argument("--state-file")
    parser.add_argument("--task-id")
    parser.add_argument("--mission-id")
    parser.add_argument("--goal-snapshot")
    parser.add_argument("--reply-contract")
    parser.add_argument("--timezone", help="IANA timezone name for reminder evaluation.")
    parser.add_argument(
        "--quiet-hours",
        help="Quiet hours window in local time, for example 22:00-08:00.",
    )
    parser.add_argument(
        "--workday-end",
        help="Local workday end time, for example 22:00.",
    )
    parser.add_argument("--deadline-minutes", type=int)
    args = parser.parse_args()

    config = load_json(Path(args.config).expanduser())
    to_email = resolve_value(args.to_email, config, "to_email", "to_email")
    from_email = resolve_value(args.from_email, config, "from_email", "from_email")
    body = args.text if args.text is not None else sys.stdin.read().strip()
    if not body:
        raise SystemExit("Email body is empty. Provide --text or pipe text via stdin.")

    msg = EmailMessage()
    msg["Subject"] = args.subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=from_email.split("@")[-1])
    msg.set_content(body)

    with open_smtp(config) as server:
        server.send_message(msg)

    sent_at = int(time.time())
    if args.state_file:
        state_path = Path(args.state_file)
        state = load_json(state_path)
        quiet_hours = args.quiet_hours or state.get("quiet_hours") or "22:00-08:00"
        state.update(
            {
                "state_version": 2,
                "channel": "email",
                "status": "awaiting_reply",
                "awaiting_reply": True,
                "completed": False,
                "reply_status": "",
                "reply_target": config.get("reply_from", to_email),
                "last_prompt": body,
                "last_sent_at": sent_at,
                "last_sent_message_id": msg["Message-ID"],
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
        save_json(state_path, state)

    print(
        json.dumps(
            {
                "ok": True,
                "to_email": to_email,
                "message_id": msg["Message-ID"],
                "sent_at": sent_at,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
