# Telegram Setup

Use this path only when the user explicitly asks for Telegram delivery.

## What works

- Send a task briefing to the user's Telegram account with `scripts/send_telegram.py`
- Poll Telegram for the user's reply with `scripts/check_telegram_reply.py`
- Mark the task complete when any non-bot text reply arrives from the target chat

## Required secrets

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

For plug-and-play use inside the DuoShe skill, save them once to:

- `~/.codex/duo-she/telegram.json`

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
python3 scripts/setup_telegram.py \
  --bot-token ... \
  --chat-id ...
```

After that, `send_telegram.py` and `check_telegram_reply.py` will read the config automatically.

## Example: send the one-hour mood check

```bash
python3 scripts/send_telegram.py \
  --state-file .duo-she-telegram-state.json \
  --text "一个小时到了，你现在心情怎么样？回复一句心情，这次测试就算完成。"
```

## Example: check whether the user replied

```bash
python3 scripts/check_telegram_reply.py \
  --state-file .duo-she-telegram-state.json
```

## Automation pattern

For a recurring Codex automation:

1. On the send run, call `scripts/send_telegram.py` and write the state file.
2. On the follow-up run, call `scripts/check_telegram_reply.py`.
3. If `completed=true`, confirm success in the thread and stop nudging.
4. If not completed, either wait longer or send a shorter nudge.
