# ngrok Setup

Use ngrok when Telegram feedback buttons need to call your local FastAPI server. Telegram requires a public HTTPS webhook URL, while the API normally runs on `http://127.0.0.1:8000`.

## 1. Start FastAPI

```powershell
python -m uvicorn job_intel.api:app --reload
```

FastAPI should be available at:

```text
http://127.0.0.1:8000
```

## 2. Install Or Update ngrok

If ngrok says the agent is too old, update it first:

```powershell
ngrok update
```

If that does not work, download the latest Windows version from:

```text
https://ngrok.com/download
```

## 3. Add Your ngrok Auth Token

Copy the auth token from the ngrok dashboard and run:

```powershell
ngrok config add-authtoken YOUR_NGROK_AUTH_TOKEN
```

Do not commit this token to git.

## 4. Start A Public HTTPS Tunnel

For the free static ngrok domain shown in the dashboard, run:

```powershell
ngrok http --url=your-static-domain.ngrok-free.app 8000
```

If you do not have a static domain, this also works, but the URL changes every time:

```powershell
ngrok http 8000
```

Keep this terminal running while testing Telegram buttons.

## 5. Register Telegram Webhook

Use the public ngrok URL without the `/api/telegram/webhook` suffix:

```powershell
python -m job_intel set-telegram-webhook --public-url https://your-static-domain.ngrok-free.app
```

Check the webhook:

```powershell
python -m job_intel telegram-webhook-info
```

Expected output should include:

```text
url=https://your-static-domain.ngrok-free.app/api/telegram/webhook
pending_update_count=0
```

## 6. Test Feedback Buttons

Send a Telegram digest, then click one of the buttons:

- `Good fit`
- `Not a fit`
- `Applied`

The button text should update after Telegram reaches the FastAPI webhook through ngrok.

## Troubleshooting

If the button does nothing:

- Confirm FastAPI is still running on port `8000`.
- Confirm ngrok is still running.
- Confirm the webhook URL points to the current ngrok URL.
- Open `http://127.0.0.1:4040` to inspect ngrok requests.
- Run `python -m job_intel telegram-webhook-info` and check `pending_update_count`.

If Telegram sends old updates after reconnecting:

```powershell
python -m job_intel telegram-webhook-info
```

Then click a new button again after the webhook is confirmed.
