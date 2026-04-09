#!/usr/bin/env python3
"""Check whether the user replied by email and mark the DuoShe task complete."""

from __future__ import annotations

import argparse
import email
import imaplib
import json
import os
from datetime import datetime, timezone
from email import policy
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import Path


def default_config_path() -> Path:
    codex_home = Path(os.getenv("CODEX_HOME", Path.home() / ".codex")).expanduser()
    return codex_home / "duo-she" / "email.json"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def resolve_value(cli_value: str | None, config: dict, key: str, label: str) -> str:
    if cli_value is not None and str(cli_value).strip():
        return str(cli_value).strip()
    value = config.get(key)
    if value is not None and str(value).strip():
        return str(value).strip()
    raise SystemExit(f"Missing {label}. Provide it explicitly or configure {default_config_path()}")


def open_imap(config: dict) -> imaplib.IMAP4:
    host = resolve_value(None, config, "imap_host", "imap_host")
    port = int(resolve_value(None, config, "imap_port", "imap_port"))
    use_ssl = bool(config.get("imap_ssl", True))
    if use_ssl:
        client: imaplib.IMAP4 = imaplib.IMAP4_SSL(host, port)
    else:
        client = imaplib.IMAP4(host, port)
    username = resolve_value(None, config, "username", "username")
    password = resolve_value(None, config, "password", "password")
    client.login(username, password)
    return client


def to_timestamp(header_value: str | None) -> int | None:
    if not header_value:
        return None
    try:
        dt = parsedate_to_datetime(header_value)
    except (TypeError, ValueError, IndexError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def extract_text(msg: email.message.EmailMessage) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                try:
                    return part.get_content().strip()
                except LookupError:
                    payload = part.get_payload(decode=True) or b""
                    return payload.decode(errors="replace").strip()
    try:
        return msg.get_content().strip()
    except LookupError:
        payload = msg.get_payload(decode=True) or b""
        return payload.decode(errors="replace").strip()


def from_matches(msg: email.message.EmailMessage, reply_from: str) -> bool:
    headers = getaddresses(msg.get_all("From", []))
    normalized = reply_from.lower()
    return any(addr.lower() == normalized for _, addr in headers)


def references_message(msg: email.message.EmailMessage, message_id: str | None) -> bool:
    if not message_id:
        return False
    refs = " ".join(msg.get_all("References", []) + msg.get_all("In-Reply-To", []))
    return message_id in refs


def classify_reply(text: str) -> str:
    lowered = text.strip().lower()
    if not lowered:
        return "freeform"
    if lowered.startswith(("done", "完成", "已完成", "做完")):
        return "done"
    if lowered.startswith(("partial", "部分", "没做完", "还差")):
        return "partial"
    if lowered.startswith(("blocked", "卡住", "受阻", "block")):
        return "blocked"
    if lowered.startswith(("reschedule", "改期", "延期", "晚点", "改到")):
        return "reschedule"
    return "freeform"


def main() -> None:
    parser = argparse.ArgumentParser(description="Check for an email reply from the target sender.")
    parser.add_argument("--config", default=str(default_config_path()))
    parser.add_argument("--state-file", default=".duo-she-email-state.json")
    parser.add_argument("--reply-from")
    parser.add_argument("--folder")
    parser.add_argument("--sample-size", type=int, default=100)
    args = parser.parse_args()

    config = load_json(Path(args.config).expanduser())
    state_path = Path(args.state_file)
    state = load_json(state_path)
    reply_from = resolve_value(args.reply_from, config, "reply_from", "reply_from").lower()
    folder = resolve_value(args.folder, config, "folder", "folder")
    last_sent_at = int(state.get("last_sent_at", 0))
    last_sent_message_id = state.get("last_sent_message_id")

    with open_imap(config) as client:
        status, _ = client.select(folder)
        if status != "OK":
            raise SystemExit(f"Could not open IMAP folder: {folder}")
        status, data = client.uid("search", None, "ALL")
        if status != "OK":
            raise SystemExit("IMAP search failed.")
        message_ids = [item for item in data[0].split() if item][-args.sample_size :]

        latest_reply = None
        latest_uid = state.get("last_uid")

        for uid in reversed(message_ids):
            uid_str = uid.decode()
            if latest_uid and int(uid_str) <= int(latest_uid):
                continue

            status, raw = client.uid("fetch", uid, "(RFC822)")
            if status != "OK" or not raw or not raw[0]:
                continue

            msg = email.message_from_bytes(raw[0][1], policy=policy.default)
            if not from_matches(msg, reply_from):
                continue

            received_at = to_timestamp(msg.get("Date")) or 0
            if received_at < last_sent_at:
                continue

            if last_sent_message_id and not references_message(msg, last_sent_message_id):
                if received_at == 0:
                    continue

            latest_reply = {
                "reply_text": extract_text(msg),
                "reply_date": received_at,
                "reply_subject": msg.get("Subject"),
                "reply_message_id": msg.get("Message-ID"),
                "reply_from": reply_from,
                "last_uid": int(uid_str),
            }
            break

    if latest_reply:
        reply_status = classify_reply(latest_reply["reply_text"])
        state.update(
            {
                "awaiting_reply": False,
                "completed": reply_status == "done",
                "status": reply_status,
                "reply_status": reply_status,
                **latest_reply,
            }
        )
    else:
        state.setdefault("awaiting_reply", True)
        state.setdefault("completed", False)
        state.setdefault("status", "awaiting_reply")
        state.setdefault("reply_status", "")

    save_json(state_path, state)

    print(
        json.dumps(
            {
                "replied": bool(latest_reply),
                "completed": state.get("completed", False),
                "awaiting_reply": state.get("awaiting_reply", False),
                "status": state.get("status"),
                "reply_status": state.get("reply_status"),
                "reply_subject": state.get("reply_subject"),
                "reply_text": state.get("reply_text"),
                "last_uid": state.get("last_uid"),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
