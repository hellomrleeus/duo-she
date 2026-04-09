#!/usr/bin/env python3
"""Check whether the user replied in Telegram and mark the DuoShe task complete."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib import error, parse, request


def default_config_path() -> Path:
    codex_home = Path(os.getenv("CODEX_HOME", Path.home() / ".codex")).expanduser()
    return codex_home / "duo-she" / "telegram.json"


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
    for name in env_names:
        value = os.getenv(name)
        if value:
            return value
    value = config.get(config_key)
    if value:
        return str(value)
    raise SystemExit(
        f"Missing {label}. Provide --{label.replace('_', '-')}, set one of: {', '.join(env_names)}, "
        f"or configure {default_config_path()}"
    )


def load_state(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def get_updates(bot_token: str, offset: int | None = None) -> dict:
    query = {"timeout": 0}
    if offset is not None:
        query["offset"] = offset
    url = (
        f"https://api.telegram.org/bot{parse.quote(bot_token, safe='')}/getUpdates?"
        f"{parse.urlencode(query)}"
    )
    req = request.Request(url, method="GET")
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Check for a Telegram reply from the target chat.")
    parser.add_argument("--bot-token")
    parser.add_argument("--chat-id")
    parser.add_argument(
        "--config",
        default=str(default_config_path()),
        help="Path to Telegram config JSON. Defaults to ~/.codex/duo-she/telegram.json",
    )
    parser.add_argument(
        "--state-file",
        default=".duo-she-telegram-state.json",
        help="JSON state file used to track last_update_id and completion state.",
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
    state_path = Path(args.state_file)
    state = load_state(state_path)

    last_update_id = state.get("last_update_id")
    offset = int(last_update_id) + 1 if last_update_id is not None else None
    updates = get_updates(bot_token, offset=offset)

    max_update_id = last_update_id
    latest_reply = None
    target_chat_id = str(chat_id)

    for item in updates.get("result", []):
        update_id = item.get("update_id")
        if update_id is not None:
            max_update_id = max(update_id, max_update_id or update_id)

        message = item.get("message") or item.get("edited_message")
        if not message:
            continue

        chat = message.get("chat") or {}
        if str(chat.get("id")) != target_chat_id:
            continue

        sender = message.get("from") or {}
        if sender.get("is_bot"):
            continue

        text = (message.get("text") or message.get("caption") or "").strip()
        if not text:
            continue

        latest_reply = {
            "reply_text": text,
            "reply_date": message.get("date"),
            "reply_message_id": message.get("message_id"),
            "reply_from": sender.get("username") or sender.get("first_name") or "unknown",
        }

    if max_update_id is not None:
        state["last_update_id"] = int(max_update_id)

    if latest_reply:
        state.update(
            {
                "awaiting_reply": False,
                "completed": True,
                **latest_reply,
            }
        )
    else:
        state.setdefault("awaiting_reply", True)
        state.setdefault("completed", False)

    save_state(state_path, state)

    print(
        json.dumps(
            {
                "completed": bool(latest_reply),
                "awaiting_reply": state.get("awaiting_reply", False),
                "reply_text": state.get("reply_text"),
                "last_update_id": state.get("last_update_id"),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
