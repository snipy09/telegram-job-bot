"""
WhatsApp Channel Automated Broadcaster Service.
100% Free WhatsApp Web / Playwright automation for posting job drops to WhatsApp Channels.
"""
import os
import asyncio
import logging
from pathlib import Path
from typing import Optional

from config import WHATSAPP_CHANNEL_URL, WHATSAPP_SESSION_PATH
from services.job_service import Job

logger = logging.getLogger(__name__)


class WhatsAppService:
    def __init__(self, session_path: str = WHATSAPP_SESSION_PATH, channel_url: str = WHATSAPP_CHANNEL_URL):
        self.session_path = Path(session_path)
        self.channel_url = channel_url
        self._lock = asyncio.Lock()

    def is_session_available(self) -> bool:
        """Check if an authenticated WhatsApp session folder exists."""
        return self.session_path.exists() and any(self.session_path.iterdir())

    async def broadcast_job(self, job: Job) -> bool:
        """
        Broadcast a job posting to the Landit WhatsApp Channel.
        Returns True if successful, False otherwise.
        """
        message_text = job.to_whatsapp_text()
        return await self.send_channel_message(message_text)

    async def send_channel_message(self, message: str) -> bool:
        """
        Automates WhatsApp Web to post a message into the configured WhatsApp Channel.
        Uses Playwright async browser automation.
        """
        if not self.is_session_available():
            logger.info("ℹ️ WhatsApp session not configured yet. Run `python setup_whatsapp.py` to link WhatsApp for free 24/7 channel automation.")
            return False

        async with self._lock:
            try:
                from playwright.async_api import async_playwright
            except ImportError:
                logger.debug("Playwright not installed. Run `pip install playwright && playwright install chromium`.")
                return False

            try:
                async with async_playwright() as p:
                    # Launch persistent browser context using saved user session
                    context = await p.chromium.launch_persistent_context(
                        user_data_dir=str(self.session_path),
                        headless=True,
                        args=[
                            "--no-sandbox",
                            "--disable-setuid-sandbox",
                            "--disable-dev-shm-usage",
                            "--disable-accelerated-2d-canvas",
                            "--disable-gpu"
                        ]
                    )
                    page = await context.new_page()

                    # Navigate to the WhatsApp Channel
                    channel_code = self.channel_url.rstrip("/").split("/")[-1]
                    target_url = f"https://web.whatsapp.com/channel/{channel_code}"
                    logger.info(f"Opening WhatsApp Channel: {target_url}")
                    
                    await page.goto(target_url, timeout=45000, wait_until="domcontentloaded")
                    await asyncio.sleep(5.0)

                    # Selector for message composer in WhatsApp Channel
                    composer_selectors = [
                        'div[contenteditable="true"][data-tab="10"]',
                        'div[contenteditable="true"][data-tab="6"]',
                        'div[contenteditable="true"][title="Type a message"]',
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

                    # Focus and type the message
                    await composer.click()
                    # Use clipboard or keyboard insert to preserve multiline markdown
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
                    
                    await asyncio.sleep(1.0)
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(3.0)

                    logger.info("✅ Successfully broadcasted job posting to WhatsApp Channel!")
                    await context.close()
                    return True

            except Exception as e:
                logger.error(f"Error posting to WhatsApp Channel: {e}")
                return False


# Singleton instance
whatsapp_service = WhatsAppService()
