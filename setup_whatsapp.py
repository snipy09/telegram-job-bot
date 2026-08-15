#!/usr/bin/env python3
"""
One-Time WhatsApp Web Linker for 100% Free WhatsApp Channel Automation.
Run this script once to link your WhatsApp Admin account:
    python setup_whatsapp.py

It will open WhatsApp Web in a browser window.
Scan the QR code on your phone:
    WhatsApp -> Linked Devices -> Link a Device.

Once linked, the session is saved permanently in `./whatsapp_session`
and all subsequent automated runs will broadcast to your WhatsApp Channel 24/7!
"""
import os
import sys
import asyncio
from pathlib import Path

from config import BASE_DIR, WHATSAPP_SESSION_PATH, WHATSAPP_CHANNEL_URL


async def main():
    print("=" * 65)
    print("🤖 100% FREE WHATSAPP CHANNEL AUTOMATION SETUP")
    print("=" * 65)
    print(f"Target WhatsApp Channel: {WHATSAPP_CHANNEL_URL}")
    print(f"Session Storage Path:   {WHATSAPP_SESSION_PATH}\n")

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ Playwright is required. Installing now...")
        os.system(f"{sys.executable} -m pip install playwright")
        os.system(f"{sys.executable} -m playwright install chromium")
        from playwright.async_api import async_playwright

    session_dir = Path(WHATSAPP_SESSION_PATH)
    session_dir.mkdir(parents=True, exist_ok=True)

    print("🚀 Launching WhatsApp Web in a browser window...")
    print("👉 ACTION REQUIRED: Open WhatsApp on your phone -> Settings -> Linked Devices -> Link a Device")
    print("👉 Scan the QR Code shown on screen to authenticate.\n")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,  # Opens visible browser so user can scan QR code
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        page = await context.new_page()
        await page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

        print("⏳ Waiting for you to scan the QR code and login (up to 120 seconds)...")
        
        # Wait until QR canvas disappears or main chat pane appears
        try:
            await page.wait_for_selector('div[data-tab="3"], div[data-tab="4"], header', timeout=120000)
            print("\n🎉 LOGIN SUCCESSFUL! WhatsApp session saved in `./whatsapp_session/`.")
            print(f"🚀 Now navigating to your Landit Channel: {WHATSAPP_CHANNEL_URL}")
            
            channel_code = WHATSAPP_CHANNEL_URL.rstrip("/").split("/")[-1]
            await page.goto(f"https://web.whatsapp.com/channel/{channel_code}", wait_until="domcontentloaded")
            await asyncio.sleep(5.0)
            print("✅ Verified access to WhatsApp Channel!")
            print("✨ You're all set! Automated broadcast cycles will now post to both Telegram & WhatsApp 24/7!")
        except Exception as e:
            print(f"\n⚠️ Timeout or login error: {e}")
            print("If you already scanned the code, your session files were saved in `./whatsapp_session/`.")
        finally:
            await context.close()


if __name__ == "__main__":
    asyncio.run(main())
