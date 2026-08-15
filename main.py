"""
Continuous 24x7 Automated Channel Broadcaster for Telegram.
Dedicated exclusively to discovering, ranking, and broadcasting
10/10 jobs, internships, and part-time developer roles directly to the channel.
"""
import asyncio
import logging
import signal
import sys
from telegram import Bot

from config import BOT_TOKEN, CHANNEL_ID, CHANNEL_POST_INTERVAL_MINUTES
from database.db import db
from services.channel_service import broadcast_jobs_to_channel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s"
)
logger = logging.getLogger("ChannelBroadcaster")


class BroadcasterDaemon:
    def __init__(self):
        self._running = True
        self.target_channel = CHANNEL_ID or "@theflashjobupdates"

    def stop(self):
        logger.info("Stopping channel broadcaster daemon...")
        self._running = False

    async def start(self):
        if not BOT_TOKEN:
            logger.error("Error: TELEGRAM_BOT_TOKEN is not configured in .env!")
            sys.exit(1)

        db.set_channel(self.target_channel)
        bot = Bot(token=BOT_TOKEN)

        try:
            me = await bot.get_me()
            logger.info(f"Connected to Telegram as @{me.username}")
            logger.info(f"Dedicated 24x7 Broadcasting Active for: {self.target_channel}")
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            sys.exit(1)

        interval_seconds = max(30, CHANNEL_POST_INTERVAL_MINUTES * 60)

        while self._running:
            try:
                logger.info(f"Starting broadcast cycle for channel {self.target_channel}...")
                posted, msg = await broadcast_jobs_to_channel(bot, limit=10, force_all=False)
                logger.info(f"Broadcast cycle complete: {msg} (Newly posted: {posted})")
            except Exception as e:
                logger.error(f"Unexpected error in broadcast cycle: {e}", exc_info=True)

            logger.info(f"Next broadcast check in {interval_seconds}s...")
            try:
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break


def main():
    daemon = BroadcasterDaemon()

    def handle_signal(sig, frame):
        daemon.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    asyncio.run(daemon.start())


if __name__ == "__main__":
    main()
