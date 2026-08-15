"""
Text message handler for Job Updates Bot without emojis.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database.db import db
from services.job_service import job_service
from keyboards.keyboards import (
    get_job_card_keyboard,
    get_alerts_menu_keyboard,
    get_back_home_keyboard
)

logger = logging.getLogger(__name__)


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages."""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user = update.effective_user
    user_id = user.id if user else 0

    if user:
        db.register_user(user_id, user.username, user.first_name)

    # 1. Alert keyword subscription input
    if context.user_data.get("awaiting_alert_keyword"):
        context.user_data["awaiting_alert_keyword"] = False
        keyword = text.strip()

        if len(keyword) < 2:
            await update.message.reply_text(
                "Keyword must be at least 2 characters.",
                reply_markup=get_back_home_keyboard()
            )
            return

        success = db.add_alert(user_id=user_id, keyword=keyword)
        if success:
            response = (
                f"<b>Job Alert Activated</b>\n\n"
                f"Tracking: {keyword}\n\n"
                "You will receive an automated notification as soon as a new matching job is posted."
            )
        else:
            response = f"You already have an active alert tracking: {keyword}"

        user_alerts = db.get_user_alerts(user_id)
        await update.message.reply_text(
            text=response,
            reply_markup=get_alerts_menu_keyboard(user_alerts),
            parse_mode=ParseMode.HTML
        )
        return

    # Clear awaiting search flag
    context.user_data["awaiting_search"] = False

    # 2. Instant Job Search
    jobs, total_count, total_pages, current_page = await job_service.search_jobs(
        query=text,
        page=1,
        per_page=1
    )

    if not jobs:
        no_res = f"No jobs found matching: {text}"
        await update.message.reply_text(
            text=no_res,
            reply_markup=get_back_home_keyboard()
        )
        return

    job = jobs[0]
    is_saved = db.is_job_saved(user_id, job.id)
    card_text = job.to_telegram_html()
    keyboard = get_job_card_keyboard(
        job_id=job.id,
        job_url=job.url,
        is_saved=is_saved,
        current_page=current_page,
        total_pages=total_count,
        query_param=text
    )

    await update.message.reply_text(
        text=card_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
