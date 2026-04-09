# Follow-Up Policy

Use this policy when the user wants the skill to keep chasing them until they report progress.

## Default escalation ladder

Assume the task has a due time. If no feedback arrives:

1. At deadline: send a gentle nudge
2. +15 minutes: send a firmer nudge
3. +45 minutes: send an urgent nudge
4. +120 minutes: send a reset message that forces a response: done, blocked, or reschedule
5. After that: repeat every 60 minutes until the user replies, pauses, or the workday ends

## Message tone by stage

- `gentle`: simple reminder and quick reply request
- `firm`: call out that silence is also a status and ask for a one-line update
- `urgent`: require one of three replies: done, blocked, or need 30 more minutes
- `reset`: stop pretending the original slot is intact; ask for an explicit reset decision
- `repeat`: short pressure ping until state changes

## State requirements

The state file should track:

- `awaiting_reply`
- `completed`
- `due_at`
- `reminder_count`
- `last_nudge_at`
- `last_nudge_stage`

Use `scripts/evaluate_follow_up.py` to decide whether a reminder is due.

Example:

```bash
python3 scripts/evaluate_follow_up.py \
  --state-file .duo-she-telegram-state.json
```

If it returns `{"action":"send",...}`, dispatch the reminder through the active channel and then call:

```bash
python3 scripts/evaluate_follow_up.py \
  --state-file .duo-she-telegram-state.json \
  --mark-sent
```
