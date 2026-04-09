# Follow-Up Policy

Use this policy when the user wants the skill to keep chasing them until they report progress.

## Reply contract

Recommend one of these replies:

- `done + evidence`
- `partial + evidence`
- `blocked + blocker`
- `reschedule + new time`

Freeform replies are acceptable, but a structured reply makes adaptation much faster.

## Default escalation ladder

Assume the task has a due time. If no feedback arrives:

1. At deadline: send a gentle nudge
2. +15 minutes: send a firmer nudge
3. +45 minutes: send an urgent nudge
4. +120 minutes: send a reset message that forces a response: done, partial, blocked, or reschedule
5. After that: repeat every 60 minutes until the user replies, pauses, or the next workday starts

## Timing policy

Use the user's local timezone.

Default timing policy:

- `timezone`: user local timezone
- `quiet_hours`: `22:00-08:00`
- `workday_end`: `22:00`

Rules:

- Do not send `firm`, `urgent`, or `repeat` reminders during quiet hours
- If a reminder becomes due during quiet hours, defer it until quiet hours end
- If a mission rolls overnight, the first morning reminder should be `reset`
- Best results come when `workday_end` matches the start of `quiet_hours`

## Message tone by stage

- `gentle`: simple reminder and quick reply request
- `firm`: call out that silence is also a status and ask for a one-line update
- `urgent`: require one of four replies: done, partial, blocked, or reschedule
- `reset`: stop pretending the original slot is intact; ask for an explicit reset decision
- `repeat`: short pressure ping until state changes

## State requirements

Campaign state should track the planning truth in `.duo-she/duo-she-state.json`.

Channel state should track the delivery truth in `.duo-she/<channel>-state.json`.

Channel state should include:

- `channel`
- `task_id`
- `mission_id`
- `due_at`
- `awaiting_reply`
- `completed`
- `status`
- `reply_status`
- `reminder_count`
- `last_nudge_at`
- `last_nudge_stage`
- `timezone`
- `quiet_hours`
- `workday_end`

Use `scripts/evaluate_follow_up.py` to decide whether a reminder is due.

Example:

```bash
python3 scripts/evaluate_follow_up.py \
  --state-file .duo-she/telegram-state.json
```

If it returns `{"action":"send",...}`, dispatch the reminder through the active channel and then call:

```bash
python3 scripts/evaluate_follow_up.py \
  --state-file .duo-she/telegram-state.json \
  --mark-sent
```

If it returns `{"action":"wait","reason":"outside-active-window",...}`, do not send yet. Wait for the next active window.
