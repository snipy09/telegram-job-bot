"""
WhatsApp Channel Automated Broadcaster Service.
100% Free WhatsApp Web / Playwright automation for posting curated job drops to WhatsApp Channels.
Features:
- Curated Top 5 Digest format
- Strictly 20 posts/day maximum (persisted in SQLite DB)
- Randomized human delays (anti-bot fingerprinting)
- 100% Anti-Ban Stealth Guard (navigator.webdriver spoofing)
"""
import os
import time
import random
import asyncio
import logging
from pathlib import Path
from typing import List, Tuple, Optional

from config import WHATSAPP_CHANNEL_URL, WHATSAPP_SESSION_PATH
from database.db import db
from services.job_service import Job, format_whatsapp_top5_digest

logger = logging.getLogger(__name__)

# Strict WhatsApp Safety & Anti-Ban Limits
MIN_COOLDOWN_SECONDS = 180   # Minimum 3 minutes gap between consecutive WhatsApp posts
MAX_DAILY_POSTS = 20         # Strict hard cap: Maximum 20 posts per day


class WhatsAppService:
    def __init__(self, session_path: str = WHATSAPP_SESSION_PATH, channel_url: str = WHATSAPP_CHANNEL_URL):
        self.session_path = Path(session_path)
        self.channel_url = channel_url
        self._lock = asyncio.Lock()
        self._last_post_timestamp: float = 0.0

    def is_session_available(self) -> bool:
        """Check if an authenticated WhatsApp session folder exists."""
        return self.session_path.exists() and any(self.session_path.iterdir())

    def _check_rate_limits(self) -> Tuple[bool, str]:
        """
        Enforce strict anti-ban WhatsApp rate limits:
        1. Minimum 3 minutes cooldown between drops
        2. Maximum 20 posts per day (enforced via SQLite DB)
        """
        # 1. Check daily hard limit in SQLite
        today_posts = db.get_whatsapp_today_posts_count()
        if today_posts >= MAX_DAILY_POSTS:
            return False, f"Daily WhatsApp limit reached ({today_posts}/{MAX_DAILY_POSTS} posts today). Safeguarding account."

        # 2. Cooldown check
        now = time.time()
        elapsed = now - self._last_post_timestamp
        if self._last_post_timestamp > 0 and elapsed < MIN_COOLDOWN_SECONDS:
            remaining = int(MIN_COOLDOWN_SECONDS - elapsed)
            return False, f"Anti-ban cooldown active: waiting {remaining}s before next WhatsApp post"

        return True, "OK"

    async def broadcast_curated_digest(self, jobs: List[Job]) -> bool:
        """
        Broadcast a curated digest message with the Top 5 Best 10/10 tech jobs/internships.
        Enforces daily cap (max 20 posts/day) and randomized human delays.
        """
        can_post, reason = self._check_rate_limits()
        if not can_post:
            logger.info(f"🛡️ WhatsApp Anti-Ban Guard: {reason}")
            return False

        # Filter for unposted 10/10 jobs on WhatsApp
        unposted_jobs = [j for j in jobs if not db.is_job_posted_to_whatsapp(j.id) and j.rating == "10/10"]
        if not unposted_jobs:
            unposted_jobs = [j for j in jobs if not db.is_job_posted_to_whatsapp(j.id)]

        if not unposted_jobs:
            logger.info("No new unposted jobs for WhatsApp curated digest.")
            return False

        top_5 = unposted_jobs[:5]
        digest_text = format_whatsapp_top5_digest(top_5)

        # Randomized natural delay before posting (15s to 45s jitter)
        pre_delay = random.uniform(15.0, 45.0)
        logger.info(f"⏳ WhatsApp Human Simulator: Natural pre-post delay ({pre_delay:.1f}s)...")
        await asyncio.sleep(pre_delay)

        success = await self.send_channel_message(digest_text)
        if success:
            now = time.time()
            self._last_post_timestamp = now
            # Mark all 5 jobs as posted to WhatsApp in DB
            for job in top_5:
                db.mark_job_posted_to_whatsapp(job.id)
            logger.info(f"✅ Posted curated Top 5 Digest to Landit Channel ({db.get_whatsapp_today_posts_count()}/{MAX_DAILY_POSTS} today)")
        return success

    async def broadcast_job(self, job: Job) -> bool:
        """
        Broadcast a single job posting to the Landit WhatsApp Channel with Anti-Ban checks.
        """
        can_post, reason = self._check_rate_limits()
        if not can_post:
            logger.info(f"🛡️ WhatsApp Anti-Ban Guard: {reason}")
            return False

        if db.is_job_posted_to_whatsapp(job.id):
            return False

        # Randomized delay (20s - 60s)
        jitter = random.uniform(20.0, 60.0)
        await asyncio.sleep(jitter)

        message_text = job.to_whatsapp_text()
        success = await self.send_channel_message(message_text)
        if success:
            now = time.time()
            self._last_post_timestamp = now
            db.mark_job_posted_to_whatsapp(job.id)
            logger.info(f"✅ Posted 10/10 job to Landit Channel ({db.get_whatsapp_today_posts_count()}/{MAX_DAILY_POSTS} today)")
        return success

    async def send_channel_message(self, message: str) -> bool:
        """
        Automates WhatsApp Web with stealth fingerprinting to safely post into Landit Channel.
        """
        if not self.is_session_available():
            logger.info("ℹ️ WhatsApp session not configured yet. Run `python setup_whatsapp.py` to link WhatsApp.")
            return False

        async with self._lock:
            try:
                from playwright.async_api import async_playwright
            except ImportError:
                logger.debug("Playwright not installed.")
                return False

            try:
                async with async_playwright() as p:
                    # Stealth Browser Context with human viewport & anti-automation flags
                    context = await p.chromium.launch_persistent_context(
                        user_data_dir=str(self.session_path),
                        headless=True,
                        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                        viewport={"width": 1280, "height": 800},
                        args=[
                            "--no-sandbox",
                            "--disable-setuid-sandbox",
                            "--disable-dev-shm-usage",
                            "--disable-blink-features=AutomationControlled",
                            "--disable-gpu"
                        ]
                    )
                    page = await context.new_page()

                    # Stealth script to mask Playwright from WhatsApp detection
                    await page.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                        window.chrome = { runtime: {} };
                    """)

                    # Navigate to Landit WhatsApp Channel
                    channel_code = self.channel_url.rstrip("/").split("/")[-1]
                    target_url = f"https://web.whatsapp.com/channel/{channel_code}"
                    logger.info(f"Opening WhatsApp Channel (Stealth Mode): {target_url}")
                    
                    await page.goto(target_url, timeout=45000, wait_until="domcontentloaded")
                    
                    # Human-like random pause (4.0s - 8.0s)
                    human_wait = random.uniform(4.0, 8.0)
                    await asyncio.sleep(human_wait)

                    # Handle any popup modal or 'View channel' button if presented by WhatsApp Web
                    for btn_text in ["View channel", "Open channel", "Follow"]:
                        try:
                            btn = page.locator(f'button:has-text("{btn_text}"), div[role="button"]:has-text("{btn_text}")').first
                            if await btn.is_visible(timeout=2000):
                                await btn.click()
                                await asyncio.sleep(2.0)
                                break
                        except Exception:
                            pass

                    # Selector for message composer in WhatsApp Channel
                    composer_selectors = [
                        'div[contenteditable="true"][data-tab="10"]',
                        'div[contenteditable="true"][data-tab="6"]',
                        'div[contenteditable="true"][title="Type an update"]',
                        'div[contenteditable="true"][title="Type a message"]',
                        'div[contenteditable="true"][aria-label="Type an update"]',
                        'div[contenteditable="true"][aria-label="Type a message"]',
                        'footer div[contenteditable="true"]',
                        'div[contenteditable="true"]'
                    ]

                    composer = None
                    for sel in composer_selectors:
                        try:
                            loc = page.locator(sel).first
                            if await loc.is_visible(timeout=3000):
                                composer = loc
                                break
                        except Exception:
                            continue

                    if not composer:
                        logger.warning("WhatsApp composer box not found. Check if the logged-in account is an Admin of the channel.")
                        await context.close()
                        return False

                    # Focus composer naturally
                    await composer.click()
                    await asyncio.sleep(random.uniform(1.0, 2.0))

                    # Paste formatted markdown
                    await page.evaluate("""
                        (text) => {
                            const dataTransfer = new DataTransfer();
                            dataTransfer.setData('text/plain', text);
                            const event = new ClipboardEvent('paste', {
                                clipboardData: dataTransfer,
                                bubbles: true,
                                cancelable: true
                            });
                            document.activeElement.dispatchEvent(event);
                        }
                    """, message)
                    
                    # Human pause before pressing Enter (1.5s - 3.0s)
                    await asyncio.sleep(random.uniform(1.5, 3.0))
                    await page.keyboard.press("Enter")
                    
                    # Wait for message dispatch
                    await asyncio.sleep(random.uniform(3.5, 6.0))

                    logger.info("✅ Successfully broadcasted curated digest to Landit Channel safely!")
                    await context.close()
                    return True

            except Exception as e:
                logger.error(f"Error posting to WhatsApp Channel: {e}")
                return False


# Singleton instance
whatsapp_service = WhatsAppService()
