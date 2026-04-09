# Telegram Setup

Use this path only when the user explicitly asks for Telegram delivery.

## What works

- Run the whole Telegram follow-up loop with `scripts/run_telegram_followup.py`
- Send a task briefing to the user's Telegram account with `scripts/send_telegram.py`
- Poll Telegram for the user's reply with `scripts/check_telegram_reply.py`
- Evaluate no-reply escalation with `scripts/evaluate_follow_up.py`
- Stop nudging as soon as a valid user reply arrives

## Required secrets

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

For plug-and-play use inside the DuoShe skill, save them once to:

- `.duo-she/telegram.json`

## How to get them

1. Create a bot with BotFather and copy the bot token.
2. Start a chat with the bot and send any message.
3. Call `getUpdates` once to discover the chat id:

```bash
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getUpdates"
```

4. Export the values:

```bash
export TELEGRAM_BOT_TOKEN=...
export TELEGRAM_CHAT_ID=...
```

Or save them once with the setup script:

```bash
cd /path/to/project
python3 scripts/setup_telegram.py \
  --bot-token ... \
  --chat-id ...
```

After that, `send_telegram.py` and `check_telegram_reply.py` will read the project-local config automatically.

## Recommended reply contract

Ask the user to reply with one of:

- `done + evidence`
- `partial + evidence`
- `blocked + blocker`
- `reschedule + new time`

Freeform replies are still accepted; the script records the latest reply text and status.

## Example: send a mission and initialize channel state

Preferred orchestration path:

```bash
python3 scripts/run_telegram_followup.py --project-root .
```

That script will:

1. read `.duo-she/duo-she-state.json`
2. send the first Telegram message when needed
3. poll for replies on later runs
4. send nudges only when `evaluate_follow_up.py` says they are due
5. write updates back to `.duo-she/duo-she-state.json` and `.duo-she/telegram-state.json`

Only drop to the lower-level scripts below if you need custom orchestration.

```bash
python3 scripts/send_telegram.py \
  --state-file .duo-she/telegram-state.json \
  --task-id speaking-day-03 \
  --mission-id M-2026-04-10-01 \
  --deadline-minutes 60 \
  --timezone Asia/Shanghai \
  --quiet-hours 22:00-08:00 \
  --workday-end 22:00 \
  --reply-contract "done + evidence | partial + evidence | blocked + blocker | reschedule + new time" \
  --text "⏱️ 60 分钟任务：录 3 段英文自我介绍。到点直接回 done / partial / blocked / reschedule，并附一句证据。"
```

## Example: check whether the user replied

```bash
python3 scripts/check_telegram_reply.py \
  --state-file .duo-she/telegram-state.json
```

## Example: decide whether another nudge is due

```bash
python3 scripts/evaluate_follow_up.py \
  --state-file .duo-she/telegram-state.json
```

## Automation pattern

For a recurring automation loop, prefer:

```bash
python3 scripts/run_telegram_followup.py --project-root .
```

Do not generate a new project-local `telegram_followup.py` wrapper unless the user explicitly asks for custom logic that the built-in orchestrator cannot express.

If you need the low-level breakdown, the built-in orchestrator is effectively doing this:

1. On the send run, call `scripts/send_telegram.py` and write the state file
2. On the follow-up run, call `scripts/check_telegram_reply.py`
3. If `awaiting_reply=false`, stop nudging and hand control back to the main DuoShe review loop
4. If still waiting, call `scripts/evaluate_follow_up.py`
5. Only send another message when the evaluator returns `{"action":"send",...}`
