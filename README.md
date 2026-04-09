# DuoShe (夺舍)

[简体中文](README.zh-CN.md)

`duo-she` is a cross-runtime AI skill for Claude Code and Codex.

It turns the model into a direct execution coach: less brainstorming, more decision-making, scoped missions, honest review, and recurring accountability when the user asks for it.

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

- `duo-she-plan.md`
- `duo-she-state.json`

These files are runtime data and should be created in the active workspace, not inside the skill folder.

## Optional Follow-Up Channels

Manual check-in is the default mode.

If the user explicitly asks for recurring follow-up, DuoShe can use:

- Codex automations in Codex
- Telegram via the local relay scripts
- Email via the local relay scripts

Telegram and email require one-time setup and local credentials.

## Repository

- GitHub: [hellomrleeus/duo-she](https://github.com/hellomrleeus/duo-she)
- Clone URL: `git@github.com:hellomrleeus/duo-she.git`
