# Task Map

Use this reference when the user wants a saved plan, a checklist, a dashboard, or ongoing accountability.

## Principle

The user should always be able to answer two questions in under ten seconds:

1. What is the whole campaign?
2. What do I do right now?

That means the task map must show both:

- the whole project structure
- the current executable mission

## State layers

Use two state layers when durable execution matters:

- `duo-she-plan.md`: human-readable campaign map and checklist
- `duo-she-state.json`: campaign state for planning truth
- `.duo-she-<channel>-state.json`: optional delivery state for Telegram, email, or automation loops

Use campaign state for:

- goal
- phases
- near-term plan
- current mission
- last review
- blockers
- progress

Use channel state for:

- due time
- reminder counters
- channel metadata
- timezone
- quiet hours
- workday end
- latest reply status

Do not mix the two layers unless the task is so small that saving state is unnecessary.

## Granularity rule

Do not explode the full project into hourly tasks upfront.

Use this default granularity:

- Whole project: phase level
- Next 3-7 days: daily checklist level
- Current day: hourly blocks
- Current block: exact mission briefing

Expand future work into hourly detail just-in-time as the user approaches it.

## Suggested `duo-she-plan.md` structure

```md
# 夺舍任务地图

## Goal
- 目标:
- 截止时间:
- 完成标准:
- 时区:

## Progress
- 总进度:
- 当前阶段:
- 最近一次复盘:
- 下次回报时间:

## Phases
- [ ] Phase 1:
- [ ] Phase 2:
- [ ] Phase 3:

## Next 7 Days
- [ ] Day 1:
- [ ] Day 2:
- [ ] Day 3:

## Today
- [ ] 09:00-10:00:
- [ ] 10:30-11:30:
- [ ] 14:00-15:00:

## Current Mission
- 任务编号:
- 时间块:
- 优先级:
- 任务:
- 交付物:
- 验收标准:
- 回报格式:
- 证据提示:

## Completed Log
- 2026-04-10:

## Blockers
- None
```

## Suggested `duo-she-state.json` shape

```json
{
  "state_version": 2,
  "goal": "",
  "deadline": "",
  "timezone": "Asia/Shanghai",
  "success_criteria": [],
  "progress_percent": 0,
  "status": "active",
  "current_phase": {
    "id": "",
    "name": "",
    "status": "active"
  },
  "phases": [
    {
      "id": "",
      "name": "",
      "status": "planned",
      "exit_criteria": []
    }
  ],
  "next_7_days": [
    {
      "date": "",
      "focus": "",
      "tasks": []
    }
  ],
  "current_mission": {
    "mission_id": "",
    "title": "",
    "start": "",
    "end": "",
    "estimated_minutes": 60,
    "priority": "high",
    "task": "",
    "deliverable": "",
    "acceptance": [],
    "evidence_hint": "",
    "reply_format": "done | partial | blocked | reschedule"
  },
  "last_review": {
    "status": "",
    "completion_percent": 0,
    "evidence_ref": "",
    "blocker_type": "",
    "notes": "",
    "next_decision": ""
  },
  "blockers": [],
  "next_check_in": ""
}
```

## Suggested channel state shape

Use `.duo-she-telegram-state.json`, `.duo-she-email-state.json`, or another channel-specific filename.

```json
{
  "state_version": 2,
  "channel": "telegram",
  "task_id": "",
  "mission_id": "",
  "goal_snapshot": "",
  "timezone": "Asia/Shanghai",
  "quiet_hours": "22:00-08:00",
  "workday_end": "22:00",
  "due_at": 0,
  "awaiting_reply": true,
  "completed": false,
  "status": "awaiting_reply",
  "reply_contract": "done + evidence | partial + evidence | blocked + blocker | reschedule + new time",
  "reply_status": "",
  "reminder_count": 0,
  "last_nudge_at": 0,
  "last_nudge_stage": "",
  "last_sent_at": 0,
  "last_prompt": "",
  "last_sent_message_id": ""
}
```

## Update rules

- Rewrite `Current Mission` every time a new work block is assigned
- Update `last_review` after every review, even when the result is blocked or rescheduled
- Update `Completed Log` after every meaningful review
- Update `Next 7 Days` only when priorities materially change
- Update phase checkboxes only when a meaningful milestone is actually cleared
- If the user falls behind, preserve the record and re-scope; do not silently rewrite history
- If persistent delivery is enabled, update the channel state after every send, reply check, and reminder send
