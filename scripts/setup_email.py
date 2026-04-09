#!/usr/bin/env python3
"""One-time SMTP/IMAP setup for the DuoShe skill."""

from __future__ import annotations

import argparse
import json
import os
import stat
from pathlib import Path


def default_config_path() -> Path:
    codex_home = Path(os.getenv("CODEX_HOME", Path.home() / ".codex")).expanduser()
    return codex_home / "duo-she" / "email.json"


def prompt_if_missing(value: str | None, label: str, default: str | None = None) -> str:
    if value is not None and str(value).strip():
        return str(value).strip()
    suffix = f" [{default}]" if default is not None else ""
    entered = input(f"Enter {label}{suffix}: ").strip()
    if entered:
        return entered
    if default is not None:
        return default
    raise SystemExit(f"{label} is required.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Save SMTP/IMAP config for DuoShe email reminders.")
    parser.add_argument("--config", default=str(default_config_path()))
    parser.add_argument("--smtp-host")
    parser.add_argument("--smtp-port", type=int)
    parser.add_argument("--smtp-security", choices=["ssl", "starttls", "none"])
    parser.add_argument("--imap-host")
    parser.add_argument("--imap-port", type=int)
    parser.add_argument("--imap-ssl", choices=["true", "false"])
    parser.add_argument("--username")
    parser.add_argument("--password")
    parser.add_argument("--from-email")
    parser.add_argument("--to-email")
    parser.add_argument("--reply-from")
    parser.add_argument("--folder")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    smtp_security = prompt_if_missing(args.smtp_security, "SMTP security", "ssl")
    default_smtp_port = {"ssl": "465", "starttls": "587", "none": "25"}[smtp_security]
    default_imap_ssl = "true"
    default_imap_port = "993"

    from_email = prompt_if_missing(args.from_email, "from email address")
    to_email = prompt_if_missing(args.to_email, "target user email address")
    username = prompt_if_missing(args.username, "login username", from_email)

    config = {
        "smtp_host": prompt_if_missing(args.smtp_host, "SMTP host"),
        "smtp_port": int(prompt_if_missing(str(args.smtp_port) if args.smtp_port else None, "SMTP port", default_smtp_port)),
        "smtp_security": smtp_security,
        "imap_host": prompt_if_missing(args.imap_host, "IMAP host"),
        "imap_port": int(prompt_if_missing(str(args.imap_port) if args.imap_port else None, "IMAP port", default_imap_port)),
        "imap_ssl": prompt_if_missing(args.imap_ssl, "Use IMAP SSL (true/false)", default_imap_ssl).lower() == "true",
        "username": username,
        "password": prompt_if_missing(args.password, "password or app password"),
        "from_email": from_email,
        "to_email": to_email,
        "reply_from": prompt_if_missing(args.reply_from, "reply-from email address", to_email),
        "folder": prompt_if_missing(args.folder, "IMAP folder", "INBOX"),
    }

    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    try:
        config_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass

    print(f"Saved email config to {config_path}")


if __name__ == "__main__":
    main()
