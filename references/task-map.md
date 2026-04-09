# Task Map

Use this reference when the user wants a saved plan, a checklist, a dashboard, or ongoing accountability.

## Principle

The user should always be able to answer two questions in under ten seconds:

1. What is the whole campaign?
2. What do I do right now?

That means the task map must show both:

- the whole project structure
- the current executable mission

## Default files

- `duo-she-plan.md`: human-readable checklist and timeline
- `duo-she-state.json`: machine-readable execution state

Only create these when the user wants durable tracking or the plan is complex enough to benefit from saved state.

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

## Progress
- 总进度:
- 当前阶段:
- 当前任务:

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
- 时间块:
- 任务:
- 交付物:
- 验收标准:

## Completed Log
- 2026-04-10:

## Blockers
- None
```

## Suggested `duo-she-state.json` shape

```json
{
  "goal": "",
  "deadline": "",
  "success_criteria": [],
  "progress_percent": 0,
  "current_phase": "",
  "current_day": "",
  "current_mission": {
    "start": "",
    "end": "",
    "task": "",
    "deliverable": "",
    "acceptance": ""
  },
  "next_check_in": "",
  "due_at": 0,
  "awaiting_reply": false,
  "reminder_count": 0,
  "last_nudge_at": 0,
  "last_nudge_stage": "",
  "blockers": [],
  "last_review": "",
  "status": "active"
}
```

## Update rules

- Rewrite `Current Mission` every time a new hour block is assigned
- Update `Completed Log` after every review
- Update `Next 7 Days` only when priorities materially change
- Update phase checkboxes only when a meaningful milestone is actually cleared
- If the user falls behind, preserve the record and re-scope; do not silently rewrite history
