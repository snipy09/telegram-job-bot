"""
Telegram Job Updates Bot - CS Students & Remote Tech Job Broadcaster.
"""
import sys
import logging
from telegram import BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    MessageHandler,
    filters,
    Application
)

from config import BOT_TOKEN, ALERT_CHECK_INTERVAL_MINUTES
from handlers.commands import (
    start_command,
    help_command,
    latest_command,
    search_command,
    alerts_command,
    saved_command,
    setchannel_command,
    post_latest_command,
    channel_command,
    filter_command,
    year_command,
    fresher_command,
    internships_command
)
from handlers.callbacks import callback_router
from handlers.inline import inline_query_handler
from handlers.messages import text_message_handler
from handlers.scheduler import check_job_alerts_task

# Configure logging
logging.basicConfig(
    format="%(asctime)s - [%(levelname)s] - %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("JobUpdatesBot")


async def post_init(application: Application):
    """Register bot commands menu on Telegram startup."""
    commands = [
        BotCommand("start", "Main Menu"),
        BotCommand("filter", "Filter by Year / Category"),
        BotCommand("year", "Filter for 2nd, 3rd, 4th years"),
        BotCommand("fresher", "Fresher roles (0 exp)"),
        BotCommand("internships", "Paid CS Internships"),
        BotCommand("latest", "Latest job postings"),
        BotCommand("search", "Search by skill or role"),
        BotCommand("alerts", "Manage keyword job alerts"),
        BotCommand("saved", "View bookmarked jobs"),
        BotCommand("channel", "Check channel connection"),
        BotCommand("post_latest", "Post latest jobs to channel"),
        BotCommand("help", "Help and documentation"),
    ]
    try:
        await application.bot.set_my_commands(commands)
        logger.info("Bot command menu registered.")
    except Exception as e:
        logger.warning(f"Could not register commands: {e}")


def main():
    """Start the Job Updates Bot."""
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("Error: TELEGRAM_BOT_TOKEN missing in .env")
        sys.exit(1)

    logger.info("Starting Job Updates Bot...")

    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Core Commands
    application.add_handler(CommandHandler(["start", "menu"], start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler(["latest", "jobs"], latest_command))
    application.add_handler(CommandHandler(["filter", "filters"], filter_command))
    application.add_handler(CommandHandler(["year", "batch"], year_command))
    application.add_handler(CommandHandler(["fresher", "freshers", "entry"], fresher_command))
    application.add_handler(CommandHandler(["internships", "internship", "intern"], internships_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler(["alerts", "alert"], alerts_command))
    application.add_handler(CommandHandler(["saved", "bookmarks"], saved_command))

    # Channel Commands
    application.add_handler(CommandHandler("setchannel", setchannel_command))
    application.add_handler(CommandHandler(["post_latest", "broadcast"], post_latest_command))
    application.add_handler(CommandHandler("channel", channel_command))

    # Callbacks
    application.add_handler(CallbackQueryHandler(callback_router))

    # Inline query handler
    application.add_handler(InlineQueryHandler(inline_query_handler))

    # Freeform text handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))

    # Background Scheduler
    if application.job_queue:
        interval_seconds = max(60, ALERT_CHECK_INTERVAL_MINUTES * 60)
        application.job_queue.run_repeating(
            check_job_alerts_task,
            interval=interval_seconds,
            first=10
        )
        logger.info(f"Alert & Channel worker scheduled every {ALERT_CHECK_INTERVAL_MINUTES} minutes.")

    logger.info("Bot is running and polling updates.")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
