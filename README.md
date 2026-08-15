# 💼 Telegram Job Updates Bot

A clean, fast, and simple Telegram bot dedicated to delivering real-time job updates, quick searches, and automated notifications for tech and remote roles.

---

## ⚡ Core Features

- **📡 Real-Time Job Updates**: Continuously aggregates new postings across **Remotive**, **RemoteOK**, **Arbeitnow**, and **Jobicy**.
- **🔔 Automated Job Alerts**: Subscribe to any keyword (e.g. `Python`, `Remote React`, `DevOps`) to receive direct Telegram notifications as soon as matching jobs go live.
- **🔍 Instant Search**: Type any role or skill in chat to view matching jobs immediately.
- **⭐ Bookmarking**: Save interesting jobs with a single tap to review later.
- **🚀 Fast Apply**: Direct link buttons to apply on company career portals.

---

## ⌨️ Bot Commands

| Command | Description |
| :--- | :--- |
| `/start` | Open Main Menu |
| `/latest` | View the newest job postings |
| `/search <keyword>` | Search jobs by skill or title |
| `/alerts` | Manage your automated job alert keywords |
| `/saved` | View your bookmarked jobs |
| `/help` | View quick guide & tips |

---

## 🚀 Quick Setup

1. Configure `.env` with your token:
   ```env
   TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the bot:
   ```bash
   python bot.py
   ```
