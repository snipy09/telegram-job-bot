"""
Command handlers for Job Updates Bot.
Plain, direct text without emojis or fluff.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database.db import db
from services.job_service import job_service
from services.channel_service import broadcast_jobs_to_channel
from keyboards.keyboards import (
    get_main_menu_keyboard,
    get_job_card_keyboard,
    get_alerts_menu_keyboard,
    get_saved_jobs_keyboard,
    get_back_home_keyboard,
    get_filter_menu_keyboard
)

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start: Display clean dashboard."""
    user = update.effective_user
    if user:
        db.register_user(user.id, user.username, user.first_name)

    greeting_name = user.first_name if user and user.first_name else "there"
    channel = db.get_channel()
    channel_info = f"\nConnected Channel: {channel}\n" if channel else ""

    welcome_text = (
        f"<b>Job Updates Bot</b>\n\n"
        f"Hello {greeting_name}. This bot provides real-time CS internships and junior developer job updates.\n"
        f"{channel_info}\n"
        "<b>Options:</b>\n"
        "- Latest Jobs: View fresh openings\n"
        "- Search: Find jobs by skill or role\n"
        "- Job Alerts: Set keyword alerts for automated DMs\n"
        "- Channel: Broadcast updates to your channel via /setchannel\n\n"
        "Select an option below:"
    )

    if update.message:
        await update.message.reply_text(text=welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode=ParseMode.HTML)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text=welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode=ParseMode.HTML)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help: Plain guide."""
    channel = db.get_channel() or "Not configured"
    help_text = (
        "<b>Commands Guide</b>\n\n"
        "<b>Job Commands:</b>\n"
        "- /latest - View the newest job postings\n"
        "- /search <keyword> - Search jobs by keyword (e.g. /search python)\n"
        "- /alerts - Manage automated job alerts\n"
        "- /saved - View bookmarked jobs\n\n"
        "<b>Channel Commands:</b>\n"
        f"- Current Channel: {channel}\n"
        "- /setchannel @YourChannel - Set channel for automated updates\n"
        "- /post_latest [count] - Manually post latest jobs to channel\n"
        "- /channel - Check channel connection status"
    )
    keyboard = get_back_home_keyboard()
    if update.message:
        await update.message.reply_text(text=help_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text=help_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def setchannel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setchannel <@channel_username or ID>."""
    if not context.args:
        text = (
            "<b>Set Broadcast Channel</b>\n\n"
            "Provide your channel username or ID.\n\n"
            "Usage: /setchannel @YourChannel\n\n"
            "Ensure the bot is added as an Administrator in your channel with 'Post Messages' permission."
        )
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return

    raw_channel = context.args[0].strip()
    if not raw_channel.startswith("@") and not raw_channel.startswith("-100") and not raw_channel.startswith("-"):
        raw_channel = f"@{raw_channel}"

    try:
        chat = await context.bot.get_chat(raw_channel)
        db.set_channel(str(chat.id if chat.id else raw_channel))
        success_msg = (
            f"<b>Channel Connected</b>\n\n"
            f"Channel: {chat.title} ({raw_channel})\n\n"
            "The bot will automatically post fresh CS student and internship updates to this channel.\n"
            "Run /post_latest 5 to post the newest jobs immediately."
        )
        await update.message.reply_text(success_msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        err_msg = (
            f"<b>Could not connect to {raw_channel}</b>\n\n"
            f"Error: {e}\n\n"
            "1. Open channel settings > Administrators.\n"
            "2. Add @Flashjobbot with 'Post Messages' permission.\n"
            f"3. Run /setchannel {raw_channel} again."
        )
        await update.message.reply_text(err_msg, parse_mode=ParseMode.HTML)


async def channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /channel: View current channel status."""
    channel = db.get_channel()
    if not channel:
        text = "No channel configured. Use /setchannel @YourChannel to connect."
    else:
        text = (
            f"<b>Channel Status</b>\n\n"
            f"Connected Channel: {channel}\n"
            "Automated posting is active.\n"
            "Use /post_latest [count] to post immediately."
        )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def post_latest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /post_latest [count]: Immediately post jobs to channel."""
    channel = db.get_channel()
    if not channel:
        await update.message.reply_text("No channel connected. Use /setchannel @YourChannel first.")
        return

    count = 5
    if context.args and context.args[0].isdigit():
        count = min(15, max(1, int(context.args[0])))

    status_msg = await update.message.reply_text(f"Posting {count} latest jobs to {channel}...")
    posted, msg = await broadcast_jobs_to_channel(context.bot, limit=count, force_all=False)

    await status_msg.edit_text(
        f"<b>Broadcast Summary</b>\n\nChannel: {channel}\nJobs Posted: {posted}\n{msg}",
        parse_mode=ParseMode.HTML
    )


async def latest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /latest: Browse newest jobs."""
    user_id = update.effective_user.id if update.effective_user else 0
    jobs, total_count, total_pages, current_page = await job_service.search_jobs(page=1, per_page=1)

    if not jobs:
        msg = "No jobs found at the moment. Please try again shortly."
        if update.message:
            await update.message.reply_text(msg, reply_markup=get_main_menu_keyboard())
        return

    job = jobs[0]
    is_saved = db.is_job_saved(user_id, job.id)
    text = job.to_telegram_html(index=current_page, total=total_count)
    keyboard = get_job_card_keyboard(
        job_id=job.id,
        job_url=job.url,
        is_saved=is_saved,
        current_page=current_page,
        total_pages=total_count,
        query_param=""
    )

    if update.message:
        await update.message.reply_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search <keyword>."""
    query = " ".join(context.args).strip() if context.args else ""
    if not query:
        prompt_text = "Send the keyword or role you want to search (e.g. Python, React, DevOps):"
        if update.message:
            context.user_data["awaiting_search"] = True
            await update.message.reply_text(prompt_text, reply_markup=get_back_home_keyboard())
        return

    user_id = update.effective_user.id if update.effective_user else 0
    jobs, total_count, total_pages, current_page = await job_service.search_jobs(query=query, page=1, per_page=1)

    if not jobs:
        no_res = f"No jobs found matching: {query}"
        if update.message:
            await update.message.reply_text(no_res, reply_markup=get_back_home_keyboard())
        return

    job = jobs[0]
    is_saved = db.is_job_saved(user_id, job.id)
    text = job.to_telegram_html()
    keyboard = get_job_card_keyboard(
        job_id=job.id,
        job_url=job.url,
        is_saved=is_saved,
        current_page=current_page,
        total_pages=total_count,
        query_param=query
    )

    if update.message:
        await update.message.reply_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /alerts: Manage automated job alert keywords."""
    user_id = update.effective_user.id if update.effective_user else 0
    alerts = db.get_user_alerts(user_id)

    if not alerts:
        text = (
            "<b>Job Alerts</b>\n\n"
            "You have no active alerts.\n"
            "Add keyword alerts (e.g. Python, React, Remote) to receive automated DM updates when a matching job is posted.\n\n"
            "Tap 'Add Keyword Alert' below to start."
        )
    else:
        text = f"<b>Active Job Alerts ({len(alerts)})</b>\n\n"
        for i, a in enumerate(alerts, 1):
            text += f"{i}. Keyword: {a['keyword']}\n"
        text += "\nYou will receive automated alerts when new matching jobs appear."

    keyboard = get_alerts_menu_keyboard(alerts)
    if update.message:
        await update.message.reply_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def saved_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /saved: View bookmarked jobs."""
    user_id = update.effective_user.id if update.effective_user else 0
    saved = db.get_saved_jobs(user_id)

    if not saved:
        text = "You have no saved jobs. Use 'Save Job' on any listing to bookmark it."
    else:
        text = f"<b>Saved Jobs ({len(saved)})</b>\n\n"
        for i, j in enumerate(saved, 1):
            comp = f" at {j['company']}" if j.get('company') else ""
            text += f"{i}. <a href=\"{j['url']}\">{j['title']}</a>{comp}\n"

    keyboard = get_saved_jobs_keyboard(saved)
    if update.message:
        await update.message.reply_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


async def filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /filter: Choose student year or role type."""
    text = (
        "<b>Filter Job Openings</b>\n\n"
        "Select your college year or category to view matching roles:\n\n"
        "- <b>2nd Year:</b> Summer & Remote Internships (2027 Batch)\n"
        "- <b>3rd Year:</b> Pre-Final Year Internships (2026 Batch)\n"
        "- <b>4th Year:</b> Final Year Internships & Campus Openings (2025 Batch)\n"
        "- <b>Fresher:</b> Entry-Level & Zero-Experience Graduate Roles\n"
        "- <b>Internships:</b> All Paid CS & Web Dev Internships\n\n"
        "Strictly 0 senior roles. Select an option below:"
    )
    keyboard = get_filter_menu_keyboard()
    if update.message:
        await update.message.reply_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def year_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /year <1|2|3|4>."""
    year = None
    if context.args and context.args[0].isdigit():
        val = int(context.args[0])
        if val in (1, 2, 3, 4):
            year = val

    if year is None:
        await filter_command(update, context)
        return

    user_id = update.effective_user.id if update.effective_user else 0
    jobs, total_count, total_pages, current_page = await job_service.search_jobs(year=year, page=1, per_page=1)

    if not jobs:
        msg = f"No active roles found for Year {year} at this moment. Please check back shortly."
        if update.message:
            await update.message.reply_text(msg, reply_markup=get_filter_menu_keyboard())
        return

    job = jobs[0]
    is_saved = db.is_job_saved(user_id, job.id)
    text = job.to_telegram_html()
    keyboard = get_job_card_keyboard(
        job_id=job.id,
        job_url=job.url,
        is_saved=is_saved,
        current_page=current_page,
        total_pages=total_count,
        query_param=f"year:{year}"
    )

    if update.message:
        await update.message.reply_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def fresher_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /fresher: 0-exp graduate & entry level roles."""
    user_id = update.effective_user.id if update.effective_user else 0
    jobs, total_count, total_pages, current_page = await job_service.search_jobs(fresher_only=True, page=1, per_page=1)

    if not jobs:
        msg = "No fresher roles found at this moment. Please check back shortly."
        if update.message:
            await update.message.reply_text(msg, reply_markup=get_main_menu_keyboard())
        return

    job = jobs[0]
    is_saved = db.is_job_saved(user_id, job.id)
    text = job.to_telegram_html()
    keyboard = get_job_card_keyboard(
        job_id=job.id,
        job_url=job.url,
        is_saved=is_saved,
        current_page=current_page,
        total_pages=total_count,
        query_param="fresher"
    )

    if update.message:
        await update.message.reply_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def internships_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /internships: Paid CS internships only."""
    user_id = update.effective_user.id if update.effective_user else 0
    jobs, total_count, total_pages, current_page = await job_service.search_jobs(internships_only=True, page=1, per_page=1)

    if not jobs:
        msg = "No internships found at this moment. Please check back shortly."
        if update.message:
            await update.message.reply_text(msg, reply_markup=get_main_menu_keyboard())
        return

    job = jobs[0]
    is_saved = db.is_job_saved(user_id, job.id)
    text = job.to_telegram_html()
    keyboard = get_job_card_keyboard(
        job_id=job.id,
        job_url=job.url,
        is_saved=is_saved,
        current_page=current_page,
        total_pages=total_count,
        query_param="internships"
    )

    if update.message:
        await update.message.reply_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
