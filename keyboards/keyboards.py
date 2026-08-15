"""
Plain inline keyboards for Job Updates Bot without emojis.
"""
from typing import List, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Generate simple menu without emojis."""
    keyboard = [
        [
            InlineKeyboardButton("Latest Jobs", callback_data="menu:latest"),
            InlineKeyboardButton("Filter by Year", callback_data="menu:filter_menu"),
        ],
        [
            InlineKeyboardButton("Fresher Roles", callback_data="filter:fresher"),
            InlineKeyboardButton("Internships", callback_data="filter:internships"),
        ],
        [
            InlineKeyboardButton("Search Jobs", callback_data="menu:search_prompt"),
            InlineKeyboardButton("Job Alerts", callback_data="menu:alerts"),
        ],
        [
            InlineKeyboardButton("Saved Jobs", callback_data="menu:saved"),
            InlineKeyboardButton("Help", callback_data="menu:help"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_filter_menu_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for filtering by student year and role type."""
    keyboard = [
        [
            InlineKeyboardButton("2nd Year Students", callback_data="filter:year:2"),
            InlineKeyboardButton("3rd Year Students", callback_data="filter:year:3"),
        ],
        [
            InlineKeyboardButton("4th Year / Final Year", callback_data="filter:year:4"),
            InlineKeyboardButton("Fresher Roles (0 Exp)", callback_data="filter:fresher"),
        ],
        [
            InlineKeyboardButton("Internships Only", callback_data="filter:internships"),
            InlineKeyboardButton("All Openings", callback_data="menu:latest"),
        ],
        [
            InlineKeyboardButton("Main Menu", callback_data="menu:home")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_job_card_keyboard(
    job_id: str,
    job_url: str,
    is_saved: bool,
    current_page: int,
    total_pages: int,
    query_param: str = ""
) -> InlineKeyboardMarkup:
    """Action bar for a job card."""
    keyboard = []

    # Apply & Save
    save_text = "Unsave" if is_saved else "Save Job"
    save_data = f"unsave:{job_id}:{current_page}:{query_param}" if is_saved else f"save:{job_id}:{current_page}:{query_param}"

    keyboard.append([
        InlineKeyboardButton("Apply Link", url=job_url),
        InlineKeyboardButton(save_text, callback_data=save_data)
    ])

    # Pagination
    if total_pages > 1:
        prev_page = current_page - 1 if current_page > 1 else total_pages
        next_page = current_page + 1 if current_page < total_pages else 1

        keyboard.append([
            InlineKeyboardButton("Prev", callback_data=f"page:{prev_page}:{query_param}"),
            InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="noop"),
            InlineKeyboardButton("Next", callback_data=f"page:{next_page}:{query_param}")
        ])

    # Bottom controls
    keyboard.append([
        InlineKeyboardButton("Search More", callback_data="menu:search_prompt"),
        InlineKeyboardButton("Main Menu", callback_data="menu:home")
    ])

    return InlineKeyboardMarkup(keyboard)


def get_alerts_menu_keyboard(alert_list: Optional[List] = None) -> InlineKeyboardMarkup:
    """Keyboard for managing keyword alert subscriptions."""
    keyboard = [
        [
            InlineKeyboardButton("Add Keyword Alert", callback_data="alert:add_prompt"),
        ]
    ]

    if alert_list:
        for alert in alert_list[:8]:
            alert_id = alert["id"]
            kw = alert["keyword"]
            keyboard.append([
                InlineKeyboardButton(f"Delete '{kw}'", callback_data=f"alert:del:{alert_id}")
            ])
        keyboard.append([
            InlineKeyboardButton("Clear All Alerts", callback_data="alert:clear_all")
        ])

    keyboard.append([
        InlineKeyboardButton("Main Menu", callback_data="menu:home")
    ])
    return InlineKeyboardMarkup(keyboard)


def get_saved_jobs_keyboard(saved_list: Optional[List] = None) -> InlineKeyboardMarkup:
    """Keyboard for bookmarked jobs."""
    keyboard = []
    if saved_list:
        for item in saved_list[:6]:
            job_id = item["job_id"]
            title = item["title"][:25]
            url = item["url"]
            keyboard.append([
                InlineKeyboardButton(f"{title}...", url=url),
                InlineKeyboardButton("Remove", callback_data=f"unsave_direct:{job_id}")
            ])

    keyboard.append([
        InlineKeyboardButton("Search Jobs", callback_data="menu:search_prompt"),
        InlineKeyboardButton("Main Menu", callback_data="menu:home")
    ])
    return InlineKeyboardMarkup(keyboard)


def get_back_home_keyboard() -> InlineKeyboardMarkup:
    """Back to home button."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Main Menu", callback_data="menu:home")
    ]])
