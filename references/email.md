# Email Setup

Use this path when the user explicitly asks for email delivery or email-based check-ins.

## What works

- Send a task briefing by SMTP with `scripts/send_email.py`
- Poll for a reply by IMAP with `scripts/check_email_reply.py`
- Mark the task complete when an incoming email from the configured reply address arrives after the task was sent

## Required configuration

Save the config once to:

- `~/.codex/duo-she/email.json`

Use:

```bash
python3 scripts/setup_email.py
```

Recommended fields:

- SMTP host, port, and security mode
- IMAP host and port
- login username and password or app password
- sender email address
- target user email address
- reply-from email address
- IMAP folder, usually `INBOX`

## Example: send a one-hour mood check

```bash
python3 scripts/send_email.py \
  --state-file .duo-she-email-state.json \
  --deadline-minutes 60 \
  --subject "夺舍测试：一小时后回我心情" \
  --text "一个小时后直接回复这封邮件，告诉我你现在心情怎么样。你一回复，这次测试就算完成。"
```

## Example: check whether the user replied

```bash
python3 scripts/check_email_reply.py \
  --state-file .duo-she-email-state.json
```

## Notes

- Prefer app passwords instead of normal mailbox passwords
- Reply detection is strongest when the user actually replies to the sent message
- If the mailbox provider rewrites headers in unusual ways, keep the fallback rule: any reply from the configured sender after `last_sent_at` counts as completion
