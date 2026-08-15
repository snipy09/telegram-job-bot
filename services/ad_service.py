"""
Monetization & Sponsored Promotion Engine.
Injects premium sponsored cards, paid career services, resume review ads,
and partner promotions seamlessly between job postings with high aesthetic standards.
"""
import html
import random
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


@dataclass
class SponsoredAd:
    id: str
    tag: str
    headline: str
    organization: str
    highlight_badge: str
    summary_bullets: List[str]
    call_to_action_text: str
    button_label: str
    target_url: str
    is_active: bool = True

    def to_telegram_html(self) -> str:
        clean_tag = html.escape(self.tag.upper())
        clean_headline = html.escape(self.headline)
        clean_org = html.escape(self.organization)
        clean_badge = html.escape(self.highlight_badge)
        clean_url = html.escape(self.target_url)
        clean_cta = html.escape(self.call_to_action_text)

        bullet_lines = "\n".join([f"└ {html.escape(b)}" for b in self.summary_bullets])

        card = (
            f"⭐ <b>SPONSORED SPOTLIGHT</b> ─── 🚀 <b>{clean_tag}</b>\n\n"
            f"<b>{clean_headline}</b>\n"
            f"🏢 <b>{clean_org}</b>\n\n"
            f"✨ {clean_badge}\n\n"
            f"──────── 📌 <b>OFFER HIGHLIGHTS</b> ────────\n\n"
            f"{bullet_lines}\n\n"
            f"─────────────────────────────────\n\n"
            f"👉 <a href=\"{clean_url}\"><b>{clean_cta}</b></a>"
        )
        return card

    def get_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(self.button_label, url=self.target_url)]
        ])


class AdService:
    def __init__(self):
        self._ads: List[SponsoredAd] = [
            SponsoredAd(
                id="ad_resume_review",
                tag="CAREER ACCELERATOR",
                headline="ATS-Proof Software Engineer Resume Review & Roast",
                organization="FlashJob Career Prep",
                highlight_badge="🎯 Top 1% Tech Mentor Review  |  ⏱ 24h Turnaround  |  ⭐ 4.9/5",
                summary_bullets=[
                    "Get your Tier-2/3 college resume optimized for Top 500 ATS scanners",
                    "Direct feedback from MAANG & Tier-1 AI startup engineers",
                    "Includes GitHub project review & LinkedIn profile makeover"
                ],
                call_to_action_text="CLICK HERE TO GET YOUR RESUME REVIEWED",
                button_label="📄 Get Your Resume Reviewed",
                target_url="https://t.me/Flashjobbot"
            ),
            SponsoredAd(
                id="ad_mock_interview",
                tag="INTERVIEW PREP",
                headline="1-on-1 Fullstack & DSA Mock Interview with Tech Leads",
                organization="TechPrep Mentorship",
                highlight_badge="💡 Real Startup Interview Questions  |  📊 Detailed Feedback Report",
                summary_bullets=[
                    "Live 60-min coding session covering DSA, System Design & Live Debugging",
                    "Tailored for 1st-4th year students targeting ₹10k-50k/mo internships & 6-15 LPA jobs",
                    "Includes actionable score sheet and recommended practice roadmap"
                ],
                call_to_action_text="CLICK HERE TO BOOK YOUR MOCK INTERVIEW",
                button_label="🎯 Book 1:1 Mock Interview",
                target_url="https://t.me/Flashjobbot"
            ),
            SponsoredAd(
                id="ad_sponsored_partner",
                tag="PARTNER SPOTLIGHT",
                headline="Promote Your Tech Product, Cohort or Open Roles Here",
                organization="FlashJob Partner Network",
                highlight_badge="📢 Reach 10,000+ Verified Indian Engineering Students & Freshers",
                summary_bullets=[
                    "Target 1st to 4th year CS/IT students actively seeking tech roles",
                    "Direct Telegram channel broadcast & interactive bot menu placement",
                    "High engagement rates for developer tools, courses, and job openings"
                ],
                call_to_action_text="CLICK HERE TO PROMOTE WITH FLASHJOB",
                button_label="📢 Book Sponsored Promotion",
                target_url="https://t.me/Flashjobbot"
            )
        ]
        self._current_index = 0

    def get_next_ad(self) -> Optional[SponsoredAd]:
        """Return the next rotating sponsored ad."""
        active_ads = [a for a in self._ads if a.is_active]
        if not active_ads:
            return None
        ad = active_ads[self._current_index % len(active_ads)]
        self._current_index += 1
        return ad

    def add_custom_ad(self, ad: SponsoredAd):
        """Add a new sponsored ad dynamically."""
        self._ads.append(ad)


ad_service = AdService()
