# ReminderBot 🚀🚀🚀

## Overview 🎯📅🔔

ReminderBot is an automated reminder system that sends WhatsApp notifications to clients who have scheduled appointments. The bot scans your calendar for events named "טיפול", extracts the client's name and phone number, and prompts you to confirm whether a reminder should be sent. If confirmed, the bot sends a reminder message to the client via WhatsApp.

## Features ⚡💡✅

- **Automated Appointment Check**: Scans calendar daily for events containing "טיפול".
- **WhatsApp Integration**: Sends reminders via the WhatsApp API.
- **User Confirmation**: Allows manual confirmation before sending messages.
- **MongoDB Storage**: Stores pending confirmations for reliability.
- **CI/CD Pipeline**: Automated testing via GitHub Actions.
- **Dockerized Deployment**: The bot runs inside a Docker container and is deployed on Render.

---

## Project Structure 📂🗂️📌

```
nirhazan35-remindersbot/
├── dockerfile
├── privacy-policy.md
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── calendar_service.py
│   ├── config.py
│   ├── initialization.py
│   ├── main.py
│   ├── pending_confirmation_manager.py
│   ├── reminder_bot.py
│   ├── whatsapp_messaging_service.py
│   └── routers/
│       ├── __init__.py
│       ├── health.py
│       ├── run_check.py
│       └── webhook.py
├── tests/
│   ├── __init__.py
│   ├── test_calendar_service.py
│   ├── test_pending_confirmation_manager.py
│   ├── test_reminder_bot.py
│   ├── test_route_health.py
│   ├── test_route_run_check.py
│   ├── test_route_webhook.py
│   └── test_whatsapp_messaging_service.py
└── .github/
    └── workflows/
        ├── ci.yaml
        └── schedule.yaml
```

---

## Setup Instructions 🛠️📝⚙️

### 1. Clone the Repository 🔽💻

```sh
git clone https://github.com/nirhazan35/RemindersBot.git
cd RemindersBot
```

### 2. Install Dependencies 📦📌✅

```sh
pip install -r requirements.txt
```

### 3. Environment Variables 🔑🔧🗂️

Create a `.env` file with the following:

```
CALENDAR_USERNAME=your_calendar_username
CALENDAR_PASSWORD=your_calendar_password
ACCESS_TOKEN=your_whatsapp_access_token
PHONE_NUMBER_ID=your_whatsapp_phone_number_id
MY_PHONE_NUMBER=your_personal_phone_number
VERSION=v21.0  # WhatsApp API version
REMINDER_BODY=Your reminder message template
VERIFY_TOKEN=your_webhook_verification_token
MONGO_URI=your_mongodb_connection_string
```

Ensure that all variables are properly set up before running the bot.

---

## Exposing Localhost for Testing with ngrok 🌍🔗⚡

If you want to test your bot locally and expose your `localhost` for webhook integrations, use **ngrok**:

### 1. Install ngrok 📥🔧

```sh
pip install pyngrok  # or download from https://ngrok.com/download
```

### 2. Start an ngrok Tunnel 🔌📡

```sh
ngrok http 5000
```

This will generate a public URL like `https://your-ngrok-url.ngrok.io`. Use this URL for setting up your webhook in the WhatsApp API settings (`https://your-ngrok-url.ngrok.io/webhook`).

---

## CI/CD Workflow 🔄🚀🛠️

### GitHub Actions Pipeline ✅⚙️📡

1. **Run Tests**: On every push to `main`, the tests inside the `tests/` folder are executed using `pytest`.
2. **Auto Deployment**: If tests pass, the bot is built using Docker and deployed to Render.
3. **Scheduled Execution**: A GitHub Actions workflow triggers `run-check` daily to process appointments.

---

## Deployment (Docker + Render) 🐳🚀🌍

### 1. Build and Run Locally 🏗️🖥️

```sh
docker build -t reminderbot .
docker run -p 5000:5000 --env-file .env reminderbot
```

### 2. Deploy to Render ☁️🚀

- Connect your GitHub repo to **Render**.
- Add environment variables in Render's dashboard.
- Render will auto-deploy on every push to `main`.

---

## WhatsApp API Integration Setup 📲🔧💬

1. **Create an App in Meta Developer Portal**:

   - Go to [Meta for Developers](https://developers.facebook.com/).
   - Create a new App and select **Business**.
   - Under "WhatsApp", create a "WhatsApp Business Account".
   - Generate a Test Phone Number.

2. **Get API Credentials**:

   - Navigate to **API settings**.
   - Copy the "Access Token" and add it to `.env` as `ACCESS_TOKEN`.
   - Copy the "Phone Number ID" and add it to `.env` as `PHONE_NUMBER_ID`.

3. **Set Up Webhooks**:

   - Go to "Webhooks" under "WhatsApp Settings".
   - Subscribe to "Message Received" events.
   - Use `{your_server_url}/webhook` as the callback URL.
   - Set `VERIFY_TOKEN` in `.env` with your chosen verification token.

---

## CalDav Calendar Integration 📅🔑🖥️

1. **Find Your CalDav URL**:

   - If using Google Calendar, enable **CalDav API** in [Google API Console](https://console.developers.google.com/).
   - If using other providers, check their documentation.

2. **Create Credentials**:

   - Use your **CalDav username and password**.
   - Store credentials in `.env` (`CALENDAR_USERNAME`, `CALENDAR_PASSWORD`).

---

## API Routes 🚀🛠️📡

| Route        | Method | Description                           |
| ------------ | ------ | ------------------------------------- |
| `/health`    | GET    | Checks if the bot is running.         |
| `/webhook`   | POST   | Receives messages from WhatsApp.      |
| `/run-check` | GET    | Manually triggers the calendar check. |

---

## Running Tests 🧪✅🛠️

```sh
pytest tests/
```

---

## Contributing 🤝💡🚀

1. Fork the repo.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit changes (`git commit -m "Added new feature"`).
4. Push (`git push origin feature-branch`).
5. Open a Pull Request.
