"""
Telegram Channel broadcasting service.
Publishes plain, direct job updates to the designated Telegram Channel.
"""
import asyncio
import logging
from typing import Tuple, Optional
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

from database.db import db
from services.job_service import job_service

logger = logging.getLogger(__name__)


async def broadcast_jobs_to_channel(bot: Bot, limit: Optional[int] = None, force_all: bool = False) -> Tuple[int, str]:
    """
    Broadcast latest unposted jobs directly to the configured Telegram Channel.
    If limit is None, posts every single new job as soon as it appears.
    Returns (posted_count, status_message).
    """
    channel_id = db.get_channel()
    if not channel_id:
        logger.info("No Telegram Channel configured for broadcasting.")
        return 0, "No channel configured. Set one using /setchannel @YourChannel"

    logger.info(f"Checking for new job updates to post to channel '{channel_id}'...")
    all_jobs = await job_service.get_all_jobs(force_refresh=True)
    if not all_jobs:
        return 0, "No job postings available."

    posted_count = 0
    for job in all_jobs:
        if limit is not None and posted_count >= limit:
            break

        if not force_all and db.is_job_posted_to_channel(job.id):
            continue

        try:
            post_text = job.to_telegram_html()

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Apply Link", url=job.url)]
            ])

            await bot.send_message(
                chat_id=channel_id,
                text=post_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )

            db.mark_job_posted_to_channel(job.id)
            posted_count += 1
            logger.info(f"Successfully posted job '{job.title}' to channel {channel_id}")

            # 20-second gap between each job posting
            await asyncio.sleep(20.0)

        except Exception as e:
            logger.error(f"Error posting job to channel {channel_id}: {e}")
            return posted_count, f"Error posting to channel: {e}"

    return posted_count, f"Posted {posted_count} job(s) to channel."
