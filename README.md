# DuoShe (夺舍)

[简体中文](README.zh-CN.md)

`duo-she` is a cross-runtime AI skill for Claude Code and Codex.

It turns the model into a direct execution coach: less brainstorming, more decision-making, scoped missions, honest review, and recurring accountability when the user asks for it.

Runtime rule: the skill files are treated as read-only. DuoShe writes all project-specific state, configs, channel secrets, reminders, and dashboards under the active project's `.duo-she/` directory.

## What It Does

- Locks vague goals into concrete, measurable outcomes
- Breaks work into phases, near-term plans, and current missions
- Pushes the user toward visible output instead of motivational fluff
- Reviews evidence honestly and adapts the next step
- Supports manual follow-up by default
- Supports Codex automation, Telegram, and email follow-up when explicitly requested

## Runtime Compatibility

This repository is designed to work in both environments:

- Claude Code: uses [`CLAUDE.md`](CLAUDE.md) as the main instruction file
- Codex: uses [`SKILL.md`](SKILL.md) plus [`agents/openai.yaml`](agents/openai.yaml) for skill discovery

The behavior is intentionally aligned across both runtimes:

- prefer runtime-neutral planning and local files first
- use platform-specific automation only when the runtime supports it
- fall back cleanly when a feature is unavailable

## How DuoShe Runs

The normal execution loop is:

1. Lock the goal, constraints, deadline, and time budget
2. Break the work into phases, a near-term plan, and the current mission
3. Give the user one concrete mission with a deliverable and acceptance check
4. Ask the user to come back with evidence
5. Classify the return as `done`, `partial`, `blocked`, or `reschedule`
6. Update the saved state and assign the next mission

If the user already provides enough context, DuoShe can use a fast path: skip the long intake, lock the spec immediately, and issue the first mission right away.

## Reply Contract

The preferred replies are:

- `done + evidence`
- `partial + evidence`
- `blocked + blocker`
- `reschedule + new time`

Freeform replies still work, but the structured contract makes adaptation and reminders much cleaner.

## Install

### Codex

Use the skill installer:

```text
Use $skill-installer to install https://github.com/hellomrleeus/duo-she
```

Or install manually from the repo:

```bash
git clone git@github.com:hellomrleeus/duo-she.git
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
ln -s /path/to/duo-she "${CODEX_HOME:-$HOME/.codex}/skills/duo-she"
```

Detailed Codex install notes live in [`.codex/INSTALL.md`](.codex/INSTALL.md).

For Telegram and email setup, run the setup scripts from the project root so the config lands in `.duo-she/`.

### Claude Code

Clone the repository and place it where Claude Code can read the skill instructions:

```bash
git clone git@github.com:hellomrleeus/duo-she.git
```

The canonical instruction file is [`CLAUDE.md`](CLAUDE.md).

## Quick Start

Example prompts:

- `夺舍，我想在 30 天内把我的英语口语练到能完成一次模拟面试`
- `Use $duo-she to take over this goal and tell me exactly what to do this hour`
- `帮我把这个项目拆成未来 7 天的执行计划，然后只给我今天第一条任务`
- `每小时盯我一次，我做完回来给你看`

Expected flow:

1. DuoShe locks the goal and constraints
2. DuoShe creates a phased plan
3. DuoShe issues the current mission
4. The user returns with evidence
5. DuoShe reviews, adapts, and assigns the next mission

## Files

- [`CLAUDE.md`](CLAUDE.md): canonical behavior spec for Claude Code and the source-of-truth instruction set
- [`SKILL.md`](SKILL.md): Codex-compatible skill entry point with aligned behavior
- [`agents/openai.yaml`](agents/openai.yaml): Codex UI metadata
- [`references/task-map.md`](references/task-map.md): task map structure for persisted plans
- [`references/telegram.md`](references/telegram.md): Telegram delivery workflow
- [`references/email.md`](references/email.md): email delivery workflow
- [`references/follow-up-policy.md`](references/follow-up-policy.md): escalation and reminder timing
- [`scripts/`](scripts/): local helpers for Telegram, email, and follow-up evaluation

## Persistence

When the task matters beyond a single reply, DuoShe can create:

- `.duo-she/duo-she-plan.md`
- `.duo-she/duo-she-state.json`
- `.duo-she/<channel>-state.json`
- `.duo-she/telegram.json`
- `.duo-she/email.json`

Use them this way:

- `.duo-she/duo-she-plan.md`: human-readable checklist and timeline
- `.duo-she/duo-she-state.json`: planning truth for phases, missions, reviews, blockers, and progress
- `.duo-she/<channel>-state.json`: delivery truth for Telegram, email, or automation reminder loops
- `.duo-she/telegram.json` and `.duo-she/email.json`: project-local channel credentials and routing config

These files are runtime data and should live under `.duo-she/` in the active project, not inside the skill folder.

## Optional Follow-Up Channels

Manual check-in is the default mode.

If the user explicitly asks for recurring follow-up, DuoShe can use:

- Codex automations in Codex
- Telegram via the built-in orchestrator `scripts/run_telegram_followup.py`
- Email via the built-in orchestrator `scripts/run_email_followup.py`

Telegram and email require one-time setup and local credentials.

Reply capture for Telegram and email is polling-based. A single run can send a message, but only later heartbeat runs can notice the user's reply.

Reminder timing is quiet-hours-aware:

- default quiet hours: `22:00-08:00`
- default workday end: `22:00`
- overnight misses reopen with a reset-style morning prompt instead of stale urgent spam

## Maintainer Workflow

`CLAUDE.md` is the canonical source file.

After editing it, regenerate `SKILL.md` with:

```bash
python3 scripts/sync_skill.py
```

To verify the mirror is clean without rewriting files:

```bash
python3 scripts/sync_skill.py --check
```

The repository also runs this check in GitHub Actions.

## Repository

- GitHub: [hellomrleeus/duo-she](https://github.com/hellomrleeus/duo-she)
- Clone URL: `git@github.com:hellomrleeus/duo-she.git`
