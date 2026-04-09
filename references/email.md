# Email Setup

Use this path when the user explicitly asks for email delivery or email-based check-ins.

## What works

- Send a task briefing by SMTP with `scripts/send_email.py`
- Poll for a reply by IMAP with `scripts/check_email_reply.py`
- Evaluate no-reply escalation with `scripts/evaluate_follow_up.py`
- Stop nudging as soon as a valid user reply arrives

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

## Recommended reply contract

Ask the user to reply with one of:

- `done + evidence`
- `partial + evidence`
- `blocked + blocker`
- `reschedule + new time`

Freeform replies are still accepted; the script records the latest reply text and status.

## Example: send a mission and initialize channel state

```bash
python3 scripts/send_email.py \
  --state-file .duo-she-email-state.json \
  --task-id speaking-day-03 \
  --mission-id M-2026-04-10-01 \
  --deadline-minutes 60 \
  --timezone Asia/Shanghai \
  --quiet-hours 22:00-08:00 \
  --workday-end 22:00 \
  --reply-contract "done + evidence | partial + evidence | blocked + blocker | reschedule + new time" \
  --subject "夺舍任务：60 分钟后给我状态" \
  --text "请在 60 分钟后直接回复这封邮件，并用 done / partial / blocked / reschedule 开头，后面补一句证据或阻塞原因。"
```

## Example: check whether the user replied

```bash
python3 scripts/check_email_reply.py \
  --state-file .duo-she-email-state.json
```

## Example: decide whether another nudge is due

```bash
python3 scripts/evaluate_follow_up.py \
  --state-file .duo-she-email-state.json
```

## Notes

- Prefer app passwords instead of normal mailbox passwords
- Reply detection is strongest when the user actually replies to the sent message
- If the mailbox provider rewrites headers in unusual ways, keep the fallback rule: any reply from the configured sender after `last_sent_at` counts as a reply
