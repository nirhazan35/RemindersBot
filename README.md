# ReminderBot 🚀🚀🚀

## Overview 🎯📅🔔

ReminderBot is an automated reminder system that sends WhatsApp notifications to clients who have scheduled appointments. The bot scans your calendar for events named "טיפול", extracts the client's name and phone number, and prompts you to confirm whether a reminder should be sent. If confirmed, the bot sends a reminder message to the client via WhatsApp.

## Features ⚡💡✅

- **Automated Appointment Check**: Scans calendar daily for events containing "טיפול".
- **WhatsApp Integration**: Sends reminders via the WhatsApp API.
- **User Confirmation**: Allows manual confirmation before sending messages.
- **MongoDB Storage**: Stores pending confirmations for reliability.
- **Dockerized Deployment**: The bot runs inside a Docker container and is deployed on Render.

---

## Technologies Used 🛠️📌

- **Programming Language**: Python (FastAPI Framework)
- **Libraries & Frameworks**:
  - `fastapi` - API framework for handling HTTP requests
  - `motor` - Async MongoDB driver
  - `python-dotenv` - Loads environment variables
  - `caldav` - Accesses and fetches calendar events
  - `uvicorn` - ASGI server for running FastAPI
  - `requests` - Sends HTTP requests (used for WhatsApp API integration)
  - `pytest` - Unit testing framework
- **Database**: MongoDB (for tracking pending confirmations)
- **Automation**: GitHub Actions (for scheduled execution)
- **Deployment**: Docker + Render

---

## Setup Instructions 🛠️📝⚙️

### 1. Clone the Repository 🔽💻

```sh
git clone https://github.com/nirhazan35/RemindersBot.git
cd RemindersBot
```

### 2. Environment Variables 🔑🔧🗂️

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

## How to Save Events in Your Calendar 📅✍️

To ensure that ReminderBot detects your appointments correctly, follow these guidelines when creating events in your calendar:

1. **Event Title Format**: The event title must start with `טיפול` followed by the client's name. For example:

   - `טיפול ישראל`
   - `טיפול יוסי כהן`

2. **Event Description**:

   - Include the client's phone number inside the event description.
   - Example:
     ```
     +972501234567
     ```

3. **Time and Date**:

   - Ensure the event is scheduled for the correct day and time.
   - The bot checks for appointments **one day in advance**.

---

## Running the Bot Locally or with Docker 🖥️🐳

You can run the bot in two ways: **locally** (with dependencies installed) or inside a **Docker container**.

### 1. Running Locally 🏗️⚙️

#### **Install Dependencies**

```sh
pip install -r requirements.txt
```

#### **Start the Application**

```sh
uvicorn app.main:app --reload
```

### 2. Running with Docker 🐳

#### **Build and Run the Container**

```sh
docker build -t reminderbot .
docker run -p 5000:5000 --env-file .env reminderbot
```

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

## Deployment (Docker + Render) 🐳🚀🌍

### Deploy to Render ☁️🚀

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

---

## License 📜⚖️🔓

MIT License. See `LICENSE` for details.

