"""
WhatsApp Channel Automated Broadcaster Service.
100% Free WhatsApp Web / Playwright automation for posting job drops to WhatsApp Channels.
Includes Anti-Ban Stealth Guard, Human Delay Simulator, and Strict Rate Limiter.
"""
import os
import time
import random
import asyncio
import logging
from pathlib import Path
from typing import Optional

from config import WHATSAPP_CHANNEL_URL, WHATSAPP_SESSION_PATH
from services.job_service import Job

logger = logging.getLogger(__name__)

# Strict WhatsApp Safety & Anti-Ban Limits
MIN_COOLDOWN_SECONDS = 180  # Minimum 3 minutes gap between consecutive WhatsApp posts
MAX_POSTS_PER_HOUR = 4     # Max 4 curated 10/10 drops per hour
MAX_POSTS_PER_DAY = 25     # Max 25 drops per day


class WhatsAppService:
    def __init__(self, session_path: str = WHATSAPP_SESSION_PATH, channel_url: str = WHATSAPP_CHANNEL_URL):
        self.session_path = Path(session_path)
        self.channel_url = channel_url
        self._lock = asyncio.Lock()
        self._last_post_timestamp: float = 0.0
        self._hourly_post_timestamps: list[float] = []
        self._daily_post_timestamps: list[float] = []

    def is_session_available(self) -> bool:
        """Check if an authenticated WhatsApp session folder exists."""
        return self.session_path.exists() and any(self.session_path.iterdir())

    def _check_rate_limits(self) -> tuple[bool, str]:
        """
        Enforce strict anti-ban WhatsApp rate limits:
        1. Minimum 3 minutes cooldown between drops
        2. Maximum 4 drops per hour
        3. Maximum 25 drops per day
        """
        now = time.time()

        # Clean up timestamps older than 1 hour / 24 hours
        self._hourly_post_timestamps = [t for t in self._hourly_post_timestamps if now - t < 3600]
        self._daily_post_timestamps = [t for t in self._daily_post_timestamps if now - t < 86400]

        # 1. Cooldown check
        elapsed = now - self._last_post_timestamp
        if self._last_post_timestamp > 0 and elapsed < MIN_COOLDOWN_SECONDS:
            remaining = int(MIN_COOLDOWN_SECONDS - elapsed)
            return False, f"Anti-ban cooldown active: waiting {remaining}s before next WhatsApp post"

        # 2. Hourly limit check
        if len(self._hourly_post_timestamps) >= MAX_POSTS_PER_HOUR:
            return False, f"Hourly WhatsApp limit reached ({MAX_POSTS_PER_HOUR}/hour). Safeguarding account."

        # 3. Daily limit check
        if len(self._daily_post_timestamps) >= MAX_POSTS_PER_DAY:
            return False, f"Daily WhatsApp limit reached ({MAX_POSTS_PER_DAY}/day). Safeguarding account."

        return True, "OK"

    async def broadcast_job(self, job: Job) -> bool:
        """
        Broadcast a job posting to the Landit WhatsApp Channel with Anti-Ban checks.
        Returns True if successful, False otherwise.
        """
        can_post, reason = self._check_rate_limits()
        if not can_post:
            logger.info(f"🛡️ WhatsApp Anti-Ban Guard: {reason}")
            return False

        message_text = job.to_whatsapp_text()
        success = await self.send_channel_message(message_text)
        if success:
            now = time.time()
            self._last_post_timestamp = now
            self._hourly_post_timestamps.append(now)
            self._daily_post_timestamps.append(now)
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
                    # Stealth Browser Context with human viewport & flags
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

                    # Stealth scripts to mask automation from WhatsApp detection
                    await page.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                        window.chrome = { runtime: {} };
                    """)

                    # Navigate to Landit WhatsApp Channel
                    channel_code = self.channel_url.rstrip("/").split("/")[-1]
                    target_url = f"https://web.whatsapp.com/channel/{channel_code}"
                    logger.info(f"Opening WhatsApp Channel (Stealth Mode): {target_url}")
                    
                    await page.goto(target_url, timeout=45000, wait_until="domcontentloaded")
                    
                    # Human-like random pause (4.0s - 7.5s)
                    human_wait = random.uniform(4.0, 7.5)
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
                    await asyncio.sleep(random.uniform(0.8, 1.8))

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
                    
                    # Human pause before pressing Enter (1.2s - 2.5s)
                    await asyncio.sleep(random.uniform(1.2, 2.5))
                    await page.keyboard.press("Enter")
                    
                    # Wait for message dispatch
                    await asyncio.sleep(random.uniform(3.0, 5.0))

                    logger.info("✅ Successfully broadcasted job posting to WhatsApp Channel safely!")
                    await context.close()
                    return True

            except Exception as e:
                logger.error(f"Error posting to WhatsApp Channel: {e}")
                return False


# Singleton instance
whatsapp_service = WhatsAppService()
