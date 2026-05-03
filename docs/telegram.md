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

## 3. Run With Environment Variables

```powershell
$env:TELEGRAM_BOT_TOKEN="your-bot-token"
$env:TELEGRAM_CHAT_ID="your-chat-id"

python -m job_intel match `
  --resume C:\path\to\resume.pdf `
  --out reports\match_report.md `
  --notify-telegram `
  --telegram-min-score 70 `
  --telegram-limit 5
```

You can also pass `--telegram-token` and `--telegram-chat-id` directly, but environment variables are safer for local development, Airflow, Docker, and Kubernetes secrets.
