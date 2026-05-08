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

The app reads `.env` and `.env.local` for local CLI/API runs. Airflow reads `airflow/.env` through Docker Compose. Real environment variables still take priority over values in `.env`.

```powershell
python -m job_intel test-telegram
```

If the bot and chat ID are correct, you should receive a Telegram message immediately.

## 4. Run the Job Pipeline With Telegram

```powershell
python -m job_intel run-pipeline `
  --resume C:\path\to\resume.pdf `
  --out reports\match_report.md `
  --notify-telegram `
  --telegram-min-score 70 `
  --telegram-limit 5
```

You can also pass `--telegram-token` and `--telegram-chat-id` directly, but environment variables are safer for local development, Airflow, Docker, and Kubernetes secrets.

Telegram digests are deduplicated by `source + external_id + chat_id`. Once a job is successfully sent to a chat, later runs skip it instead of pushing the same opportunity again.

Each digest item includes the job title, company, source, location, score, recommendation reason, matched skills, missing skills, compact summary, and direct job URL.

When LLM analysis is enabled, Telegram digests also include the LLM fit score, recommendation note, and concerns.

## 5. Enable Feedback Buttons

Telegram job messages include feedback buttons:

- `Good fit`: record that the job is interesting.
- `Not a fit`: stop sending that job again.
- `Applied`: stop sending that job again after you apply.

Button clicks are handled by the FastAPI webhook endpoint:

```text
/api/telegram/webhook
```

Telegram must reach that endpoint through a public HTTPS URL. For a free fixed URL without buying a domain, reserve one free static domain in ngrok, then run:

```powershell
ngrok config add-authtoken <NGROK_AUTHTOKEN>
ngrok http --domain=<YOUR_STATIC_DOMAIN>.ngrok-free.app 8000
```

With the FastAPI server running on port 8000, register the webhook:

```powershell
python -m job_intel set-telegram-webhook --public-url https://<YOUR_STATIC_DOMAIN>.ngrok-free.app
```

Check the registered webhook:

```powershell
python -m job_intel telegram-webhook-info
```

After the webhook is registered, clicking `Not a fit` or `Applied` stores feedback in SQLite and future Telegram runs skip that job for the same chat.
