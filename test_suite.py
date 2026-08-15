"""
Test suite for Superior Multi-Source Scraper & Time-Filtered Broadcaster.
"""
import os
import tempfile
import asyncio
import unittest

from database.db import Database
from services.job_service import JobService


class TestJobUpdatesAndChannel(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.db = Database(db_path=self.temp_db_path)
        self.job_service = JobService()

    def tearDown(self):
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_database_channel_settings(self):
        """Test channel configuration and deduplication."""
        self.db.set_channel("@test_cs_internships")
        self.assertEqual(self.db.get_channel(), "@test_cs_internships")

        # Test channel job deduplication
        self.assertFalse(self.db.is_job_posted_to_channel("job_xyz"))
        self.db.mark_job_posted_to_channel("job_xyz")
        self.assertTrue(self.db.is_job_posted_to_channel("job_xyz"))

    def test_database_alerts_and_saved(self):
        """Test student alerts and bookmarks."""
        self.db.register_user(100, "alice", "Alice")
        self.assertTrue(self.db.add_alert(100, "Python Intern"))
        self.assertTrue(self.db.save_job(100, "job_1", "Software Engineer Intern", "Acme", "https://example.com"))
        
        self.assertEqual(len(self.db.get_user_alerts(100)), 1)
        self.assertEqual(len(self.db.get_saved_jobs(100)), 1)

    async def test_job_service_scraping_and_template(self):
        """Test multi-source scraping, template format, and Indian student filtering."""
        jobs = await self.job_service.get_all_jobs()
        self.assertGreater(len(jobs), 0)
        
        first_job = jobs[0]
        self.assertIsNotNone(first_job.title)
        self.assertIsNotNone(first_job.company)
        self.assertIsNotNone(first_job.skills_required)

        # Verify template structure
        html_msg = first_job.to_telegram_html()
        self.assertTrue("ALERT" in html_msg)
        self.assertTrue("🏢" in html_msg)
        self.assertTrue("Quick Overview:" in html_msg)
        self.assertTrue("Eligibility:" in html_msg)
        # Verify WhatsApp template structure
        wa_msg = first_job.to_whatsapp_text()
        self.assertTrue("ALERT" in wa_msg)
        self.assertTrue("🏢" in wa_msg)
        self.assertTrue("Quick Overview:" in wa_msg)
        self.assertTrue("Core Skills:" in wa_msg)
        self.assertTrue("Join Landit on WhatsApp" in wa_msg)

        # Verify WhatsApp Top 5 Digest format
        from services.job_service import format_whatsapp_top5_digest
        digest = format_whatsapp_top5_digest(jobs[:5])
        self.assertTrue("TOP 5 CURATED TECH OPPORTUNITIES" in digest)
        self.assertTrue("1️⃣" in digest)

    def test_whatsapp_daily_limits(self):
        """Test WhatsApp 20 posts/day hard cap enforcement."""
        self.assertTrue(self.db.can_post_to_whatsapp_today(max_daily=20))
        for i in range(20):
            self.db.mark_job_posted_to_whatsapp(f"job_{i}")
        self.assertFalse(self.db.can_post_to_whatsapp_today(max_daily=20))
        self.assertEqual(self.db.get_whatsapp_today_posts_count(), 20)

    def test_minimum_10k_stipend_filter(self):
        """Test strict minimum 10k stipend requirement."""
        # Must reject < 10k
        self.assertFalse(self.job_service._is_high_quality_stipend("₹5,000 /month"))
        self.assertFalse(self.job_service._is_high_quality_stipend("₹8,000 /month"))
        self.assertFalse(self.job_service._is_high_quality_stipend("5k-8k /month"))
        self.assertFalse(self.job_service._is_high_quality_stipend("Unpaid"))
        self.assertFalse(self.job_service._is_high_quality_stipend("Performance based"))

        # Must accept >= 10k
        self.assertTrue(self.job_service._is_high_quality_stipend("₹10,000 /month"))
        self.assertTrue(self.job_service._is_high_quality_stipend("₹15,000 - 25,000 /month"))
        self.assertTrue(self.job_service._is_high_quality_stipend("10k - 20k /month"))
        self.assertTrue(self.job_service._is_high_quality_stipend("$500 /month"))


if __name__ == "__main__":
    unittest.main()
