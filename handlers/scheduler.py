"""
Background scheduled tasks for job alerts and channel broadcasts without emojis.
"""
import asyncio
import logging
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from database.db import db
from services.job_service import job_service
from services.channel_service import broadcast_jobs_to_channel

logger = logging.getLogger(__name__)


async def check_job_alerts_task(context: ContextTypes.DEFAULT_TYPE):
    """
    Background worker executed periodically.
    1. Checks user keyword alerts.
    2. Automatically publishes new jobs to the broadcast channel.
    """
    logger.info("Executing scheduled job alert and channel broadcast cycle...")
    try:
        # 1. Fetch fresh jobs
        all_jobs = await job_service.get_all_jobs(force_refresh=True)
        if not all_jobs:
            return

        # 2. Channel Broadcast (Post every single newly discovered unposted job immediately)
        channel_id = db.get_channel()
        if channel_id:
            try:
                posted, msg = await broadcast_jobs_to_channel(context.bot, limit=None, force_all=False)
                if posted > 0:
                    logger.info(f"Auto-broadcasted {posted} new job(s) to channel '{channel_id}'.")
            except Exception as chan_err:
                logger.warning(f"Auto channel broadcast error: {chan_err}")

        # 3. User DMs (Keyword Alerts)
        all_alerts = db.get_all_alerts()
        if not all_alerts:
            return

        for alert in all_alerts:
            user_id = alert["user_id"]
            keyword = alert["keyword"].strip().lower()

            matches = [j for j in all_jobs if j.matches_query(keyword)]

            notified_count = 0
            for job in matches[:5]:
                if notified_count >= 3:
                    break

                if not db.is_job_notified(user_id, job.id):
                    try:
                        alert_text = (
                            f"<b>JOB ALERT MATCH</b>\n"
                            f"Matches keyword: {keyword}\n\n"
                            f"{job.to_telegram_html()}"
                        )

                        keyboard = InlineKeyboardMarkup([
                            [
                                InlineKeyboardButton("Apply Link", url=job.url),
                                InlineKeyboardButton("Save Job", callback_data=f"save:{job.id}:1:{keyword}")
                            ],
                            [
                                InlineKeyboardButton("Manage Alerts", callback_data="menu:alerts"),
                                InlineKeyboardButton("Main Menu", callback_data="menu:home")
                            ]
                        ])

                        await context.bot.send_message(
                            chat_id=user_id,
                            text=alert_text,
                            reply_markup=keyboard,
                            parse_mode=ParseMode.HTML
                        )

                        db.mark_job_notified(user_id, job.id)
                        notified_count += 1
                        logger.info(f"Delivered job alert '{job.title}' to user {user_id}")

                        await asyncio.sleep(0.15)
                    except Exception as send_err:
                        logger.warning(f"Failed to send alert to user {user_id}: {send_err}")

    except Exception as e:
        logger.error(f"Error in job alerts/broadcast task: {e}", exc_info=True)
