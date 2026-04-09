#!/usr/bin/env python3
"""One-time Telegram setup for the DuoShe skill."""

from __future__ import annotations

import argparse
import json
import stat
from pathlib import Path


def default_config_path() -> Path:
    return Path(".duo-she") / "telegram.json"


def prompt_if_missing(value: str | None, label: str) -> str:
    if value:
        return value.strip()
    entered = input(f"Enter {label}: ").strip()
    if not entered:
        raise SystemExit(f"{label} is required.")
    return entered


def main() -> None:
    parser = argparse.ArgumentParser(description="Save Telegram bot config for DuoShe.")
    parser.add_argument("--bot-token", help="Telegram bot token from BotFather")
    parser.add_argument("--chat-id", help="Telegram chat id to notify")
    parser.add_argument(
        "--config",
        default=str(default_config_path()),
        help="Where to save the config JSON. Defaults to .duo-she/telegram.json in the project.",
    )
    args = parser.parse_args()

    config_path = Path(args.config).expanduser()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    bot_token = prompt_if_missing(args.bot_token, "Telegram bot token")
    chat_id = prompt_if_missing(args.chat_id, "Telegram chat id")

    config = {
        "bot_token": bot_token,
        "chat_id": str(chat_id),
    }
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    try:
        config_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass

    print(f"Saved Telegram config to {config_path}")


if __name__ == "__main__":
    main()
