"""
Inline query search handler for Job Updates Bot without emojis.
"""
import logging
from telegram import (
    Update,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from services.job_service import job_service

logger = logging.getLogger(__name__)


async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline searches: @Flashjobbot <query>"""
    query = update.inline_query.query.strip() if update.inline_query else ""

    jobs, _, _, _ = await job_service.search_jobs(
        query=query if query else None,
        page=1,
        per_page=8
    )

    results = []
    for job in jobs:
        message_text = job.to_telegram_html()
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Apply Link", url=job.url)]
        ])

        description = f"{job.company} | {job.location}"
        if job.salary:
            description += f" | {job.salary}"

        results.append(
            InlineQueryResultArticle(
                id=job.id,
                title=job.title,
                description=description,
                input_message_content=InputTextMessageContent(
                    message_text=message_text,
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=reply_markup
            )
        )

    await update.inline_query.answer(results, cache_time=30, is_personal=True)
