"""
Configuration module for Telegram Job Bot.
Loads settings from environment variables and .env file.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

# Bot credentials
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

# Telegram Channel for Automated Broadcasts (e.g. @YourChannel or -100xxxxxxxxxx)
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "").strip()

# WhatsApp Channel Automation (100% Free)
WHATSAPP_CHANNEL_URL = os.getenv("WHATSAPP_CHANNEL_URL", "https://whatsapp.com/channel/0029Vb88acW7j6g7C5G2b83c").strip()
WHATSAPP_SESSION_PATH = os.getenv("WHATSAPP_SESSION_PATH", str(BASE_DIR / "whatsapp_session"))

# Database
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "jobs_bot.db"))

# Intervals & Caching (2 minutes for instant 24x7 real-time monitoring)
ALERT_CHECK_INTERVAL_MINUTES = int(os.getenv("ALERT_CHECK_INTERVAL_MINUTES", "2"))
CHANNEL_POST_INTERVAL_MINUTES = int(os.getenv("CHANNEL_POST_INTERVAL_MINUTES", "2"))
JOBS_CACHE_TTL_SECONDS = int(os.getenv("JOBS_CACHE_TTL_SECONDS", "120"))
JOBS_PER_PAGE = int(os.getenv("JOBS_PER_PAGE", "5"))

# Max job age filter (in hours) - e.g. only post jobs posted in the last 2 hours
MAX_JOB_AGE_HOURS = float(os.getenv("MAX_JOB_AGE_HOURS", "2.0"))

# Default User-Agent for Job API requests
HTTP_USER_AGENT = "Mozilla/5.0 (compatible; TelegramJobBot/1.0; +https://t.me/)"
