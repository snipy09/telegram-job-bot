"""
Standalone Cron Broadcaster for GitHub Actions / Scheduled Serverless Execution.
Scrapes 116+ verified tech sources and broadcasts new unposted opportunities directly to Telegram.
"""
import asyncio
import logging
import sys
from telegram import Bot

from config import BOT_TOKEN, CHANNEL_ID
from database.db import db
from services.channel_service import broadcast_jobs_to_channel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s"
)
logger = logging.getLogger("CronBroadcaster")


async def run_broadcast():
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is missing!")
        sys.exit(1)

    # Ensure target channel is configured in DB
    target_channel = CHANNEL_ID or "@theflashjobupdates"
    db.set_channel(target_channel)
    logger.info(f"Target broadcast channel: {target_channel}")

    bot = Bot(token=BOT_TOKEN)
    try:
        me = await bot.get_me()
        logger.info(f"Connected to bot @{me.username}")
    except Exception as e:
        logger.error(f"Bot authentication failed: {e}")
        sys.exit(1)

    logger.info("Executing scraping across 116+ sources and broadcasting unposted jobs...")
    posted, msg = await broadcast_jobs_to_channel(bot, limit=10, force_all=False)
    logger.info(f"Cycle completed: {msg} (Total posted: {posted})")


if __name__ == "__main__":
    asyncio.run(run_broadcast())
