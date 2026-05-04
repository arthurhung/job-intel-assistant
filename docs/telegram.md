# Telegram Notification Setup

The CLI can send the best job matches to Telegram after generating a match report.

## 1. Create a Bot

1. Open Telegram and message `@BotFather`.
2. Run `/newbot`.
3. Copy the bot token.

## 2. Get Your Chat ID

1. Send any message to your new bot.
2. Open this URL in a browser, replacing `<TOKEN>` with your bot token:

```text
https://api.telegram.org/bot<TOKEN>/getUpdates
```

3. Copy `message.chat.id` from the response.

## 3. Send a Test Message

Copy `.env.example` to `.env`, then fill in:

```powershell
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

The app reads `.env` and `.env.local` for local CLI/API runs. Telegram commands can also reuse `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` from `airflow/.env`. Airflow reads `airflow/.env` through Docker Compose. Real environment variables still take priority over values in `.env`.

```powershell
python -m job_intel test-telegram
```

If the bot and chat ID are correct, you should receive a Telegram message immediately.

## 4. Run the Job Pipeline With Telegram

```powershell
python -m job_intel run-pipeline `
  --source taiwan `
  --resume C:\path\to\resume.pdf `
  --out reports\match_report.md `
  --notify-telegram `
  --telegram-min-score 70 `
  --telegram-limit 5
```

You can also pass `--telegram-token` and `--telegram-chat-id` directly, but environment variables are safer for local development, Airflow, Docker, and Kubernetes secrets.

Telegram digests are deduplicated by `source + external_id + chat_id`. Once a job is successfully sent to a chat, later runs skip it instead of pushing the same opportunity again.
