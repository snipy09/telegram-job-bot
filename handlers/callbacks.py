"""
Callback query handlers for Job Updates Bot without emojis.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database.db import db
from services.job_service import job_service
from keyboards.keyboards import (
    get_main_menu_keyboard,
    get_job_card_keyboard,
    get_alerts_menu_keyboard,
    get_saved_jobs_keyboard,
    get_back_home_keyboard,
    get_filter_menu_keyboard
)
from handlers.commands import start_command, help_command, alerts_command, saved_command

logger = logging.getLogger(__name__)


async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route all callback queries."""
    query = update.callback_query
    if not query or not query.data:
        return

    data = query.data
    user_id = query.from_user.id

    try:
        # Navigation
        if data == "menu:home":
            await query.answer()
            await start_command(update, context)

        elif data == "menu:help":
            await query.answer()
            await help_command(update, context)

        elif data == "menu:alerts":
            await query.answer()
            await alerts_command(update, context)

        elif data == "menu:saved":
            await query.answer()
            await saved_command(update, context)

        elif data == "menu:search_prompt":
            await query.answer()
            context.user_data["awaiting_search"] = True
            prompt = "Type any skill, role, or company name to search (e.g. Python, React, DevOps):"
            await query.edit_message_text(text=prompt, reply_markup=get_back_home_keyboard())

        elif data == "menu:latest":
            await query.answer("Fetching latest jobs...")
            await render_job_page(query, context, query_param="", page=1)

        elif data == "menu:filter_menu":
            await query.answer()
            filter_text = (
                "<b>Filter Job Openings</b>\n\n"
                "Select your college year or category to view matching roles:\n\n"
                "- <b>2nd Year:</b> Summer & Remote Internships (2027 Batch)\n"
                "- <b>3rd Year:</b> Pre-Final Year Internships (2026 Batch)\n"
                "- <b>4th Year:</b> Final Year Internships & Campus Openings (2025 Batch)\n"
                "- <b>Fresher:</b> Entry-Level & Zero-Experience Graduate Roles\n"
                "- <b>Internships:</b> All Paid CS & Web Dev Internships\n\n"
                "Strictly 0 senior roles. Select an option below:"
            )
            await query.edit_message_text(text=filter_text, reply_markup=get_filter_menu_keyboard(), parse_mode=ParseMode.HTML)

        elif data.startswith("filter:year:"):
            year = int(data.split(":", 2)[2])
            await query.answer(f"Fetching Year {year} roles...")
            await render_job_page(query, context, query_param=f"year:{year}", page=1)

        elif data == "filter:fresher":
            await query.answer("Fetching Fresher roles...")
            await render_job_page(query, context, query_param="fresher", page=1)

        elif data == "filter:internships":
            await query.answer("Fetching Internships...")
            await render_job_page(query, context, query_param="internships", page=1)

        # Pagination
        elif data.startswith("page:"):
            await query.answer()
            parts = data.split(":", 2)
            page = int(parts[1])
            query_param = parts[2] if len(parts) > 2 else ""
            await render_job_page(query, context, query_param=query_param, page=page)

        elif data == "noop":
            await query.answer("Current Page", show_alert=False)

        # Bookmarks (Save / Unsave)
        elif data.startswith("save:"):
            parts = data.split(":", 3)
            job_id = parts[1]
            page = int(parts[2])
            query_param = parts[3] if len(parts) > 3 else ""

            job = await job_service.get_job_by_id(job_id)
            if job:
                db.save_job(user_id, job.id, job.title, job.company, job.url)
                await query.answer("Job saved to bookmarks.", show_alert=False)
                await render_job_page(query, context, query_param=query_param, page=page)

        elif data.startswith("unsave:"):
            parts = data.split(":", 3)
            job_id = parts[1]
            page = int(parts[2])
            query_param = parts[3] if len(parts) > 3 else ""

            db.remove_saved_job(user_id, job_id)
            await query.answer("Job removed from saved list.", show_alert=False)
            await render_job_page(query, context, query_param=query_param, page=page)

        elif data.startswith("unsave_direct:"):
            job_id = data.split(":", 1)[1]
            db.remove_saved_job(user_id, job_id)
            await query.answer("Removed.")
            await saved_command(update, context)

        # Alerts
        elif data == "alert:add_prompt":
            await query.answer()
            context.user_data["awaiting_alert_keyword"] = True
            prompt = (
                "<b>Add Job Alert</b>\n\n"
                "Send the keyword or skill you want alerts for (e.g. Python, React, Golang, Remote):\n\n"
                "You will receive an automated message as soon as a matching job is found."
            )
            await query.edit_message_text(text=prompt, reply_markup=get_back_home_keyboard(), parse_mode=ParseMode.HTML)

        elif data.startswith("alert:del:"):
            alert_id = int(data.split(":", 2)[2])
            db.delete_alert(user_id, alert_id)
            await query.answer("Alert deleted.")
            await alerts_command(update, context)

        elif data == "alert:clear_all":
            db.clear_user_alerts(user_id)
            await query.answer("All alerts deleted.")
            await alerts_command(update, context)

    except Exception as e:
        logger.error(f"Callback error: {e}", exc_info=True)
        try:
            await query.answer("Please try again.")
        except Exception:
            pass


async def render_job_page(query, context, query_param: str = "", page: int = 1):
    """Helper to render job card views with year/fresher filtering."""
    user_id = query.from_user.id
    
    # Parse filter query params
    search_q = None
    internships_only = False
    fresher_only = False
    year = None

    if query_param.startswith("year:"):
        year = int(query_param.split(":", 1)[1])
    elif query_param == "fresher":
        fresher_only = True
    elif query_param == "internships":
        internships_only = True
    elif query_param:
        search_q = query_param

    jobs, total_count, total_pages, current_page = await job_service.search_jobs(
        query=search_q,
        internships_only=internships_only,
        fresher_only=fresher_only,
        year=year,
        page=page,
        per_page=1
    )

    if not jobs:
        filter_label = f"Year {year}" if year else ("Fresher" if fresher_only else ("Internships" if internships_only else query_param))
        msg = f"No jobs found matching: {filter_label}" if filter_label else "No jobs found right now."
        await query.edit_message_text(text=msg, reply_markup=get_filter_menu_keyboard())
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
        query_param=query_param
    )

    try:
        await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    except Exception:
        pass
