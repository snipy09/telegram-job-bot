"""
Simple, efficient database layer for Telegram Job Updates Bot.
Handles users, alert subscriptions, bookmarks, channel broadcasts, and notification deduplication.
"""
import sqlite3
import logging
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Generator
from pathlib import Path
from config import DB_PATH, CHANNEL_ID

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager to ensure connections and transactions are cleanly closed."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database schema tables and indexes."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as conn:
            cursor = conn.cursor()

            # Users
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Channel settings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channel_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            # Channel posted jobs tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channel_posted_jobs (
                    job_id TEXT PRIMARY KEY,
                    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # WhatsApp Channel posted tracking (Daily cap & deduplication)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS whatsapp_posted_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT,
                    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Job alert subscriptions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    keyword TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id),
                    UNIQUE(user_id, keyword)
                )
            """)

            # Saved / Bookmarked jobs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS saved_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    job_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    url TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id),
                    UNIQUE(user_id, job_id)
                )
            """)

            # Notified jobs to avoid sending duplicate user alerts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notified_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    job_id TEXT NOT NULL,
                    notified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id),
                    UNIQUE(user_id, job_id)
                )
            """)

            # Seed default channel from config if provided
            if CHANNEL_ID:
                cursor.execute("""
                    INSERT INTO channel_settings (key, value)
                    VALUES ('broadcast_channel', ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """, (CHANNEL_ID,))

            # Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_user ON alerts(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_saved_user ON saved_jobs(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notified_user_job ON notified_jobs(user_id, job_id)")

    # Channel Methods
    def set_channel(self, channel_id: str):
        """Set or update the broadcast channel ID."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO channel_settings (key, value)
                VALUES ('broadcast_channel', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (channel_id.strip(),))

    def get_channel(self) -> Optional[str]:
        """Get current broadcast channel ID."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM channel_settings WHERE key = 'broadcast_channel'")
            row = cursor.fetchone()
            if row and row["value"]:
                return row["value"]
            return CHANNEL_ID if CHANNEL_ID else None

    def mark_job_posted_to_channel(self, job_id: str):
        """Record that a job was posted to the broadcast channel."""
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO channel_posted_jobs (job_id)
                    VALUES (?)
                """, (job_id,))
        except Exception as e:
            logger.error(f"Error marking job posted to channel: {e}")

    def is_job_posted_to_channel(self, job_id: str) -> bool:
        """Check if job has already been posted to the channel."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM channel_posted_jobs WHERE job_id = ?", (job_id,))
            return cursor.fetchone() is not None

    # User Methods
    def register_user(self, user_id: int, username: Optional[str], first_name: Optional[str]):
        """Register or update user in database."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (user_id, username, first_name, is_active)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    is_active = 1
            """, (user_id, username or "", first_name or ""))

    # Alert Methods
    def add_alert(self, user_id: int, keyword: str) -> bool:
        """Subscribe user to job updates for a keyword."""
        clean_keyword = keyword.strip().lower()
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO alerts (user_id, keyword)
                    VALUES (?, ?)
                """, (user_id, clean_keyword))
                return True
        except sqlite3.IntegrityError:
            return False

    def get_user_alerts(self, user_id: int) -> List[Dict[str, Any]]:
        """Retrieve all active alert subscriptions for a user."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM alerts WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def delete_alert(self, user_id: int, alert_id: int) -> bool:
        """Delete an alert by ID."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM alerts WHERE id = ? AND user_id = ?", (alert_id, user_id))
            return cursor.rowcount > 0

    def clear_user_alerts(self, user_id: int) -> int:
        """Clear all alerts for a user."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM alerts WHERE user_id = ?", (user_id,))
            return cursor.rowcount

    def get_all_alerts(self) -> List[Dict[str, Any]]:
        """Fetch all alerts across all users."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT a.*, u.first_name FROM alerts a JOIN users u ON a.user_id = u.user_id WHERE u.is_active = 1")
            return [dict(row) for row in cursor.fetchall()]

    # Saved Job Bookmarks
    def save_job(self, user_id: int, job_id: str, title: str, company: str, url: str) -> bool:
        """Bookmark a job for a user."""
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO saved_jobs (user_id, job_id, title, company, url)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, job_id, title, company, url))
                return True
        except sqlite3.IntegrityError:
            return False

    def remove_saved_job(self, user_id: int, job_id: str) -> bool:
        """Remove a bookmarked job."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM saved_jobs WHERE user_id = ? AND job_id = ?", (user_id, job_id))
            return cursor.rowcount > 0

    def is_job_saved(self, user_id: int, job_id: str) -> bool:
        """Check if job is saved by user."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM saved_jobs WHERE user_id = ? AND job_id = ?", (user_id, job_id))
            return cursor.fetchone() is not None

    def get_saved_jobs(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all saved jobs for a user."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM saved_jobs WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    # Notification Tracking
    def mark_job_notified(self, user_id: int, job_id: str):
        """Record that an alert was sent for a job to prevent duplicate notifications."""
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO notified_jobs (user_id, job_id)
                    VALUES (?, ?)
                """, (user_id, job_id))
        except Exception as e:
            logger.error(f"Error marking job notified: {e}")

    def is_job_notified(self, user_id: int, job_id: str) -> bool:
        """Check if user has already received an alert for this job."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM notified_jobs WHERE user_id = ? AND job_id = ?", (user_id, job_id))
            return cursor.fetchone() is not None

    # WhatsApp Channel Broadcast Tracking & Daily Cap Enforcement
    def mark_job_posted_to_whatsapp(self, job_id: str):
        """Record that a job was posted to the WhatsApp Channel."""
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO whatsapp_posted_jobs (job_id)
                    VALUES (?)
                """, (job_id,))
        except Exception as e:
            logger.error(f"Error recording WhatsApp post: {e}")

    def is_job_posted_to_whatsapp(self, job_id: str) -> bool:
        """Check if a job was already broadcasted to WhatsApp."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM whatsapp_posted_jobs WHERE job_id = ?", (job_id,))
            return cursor.fetchone() is not None

    def get_whatsapp_today_posts_count(self) -> int:
        """Get total number of posts made to WhatsApp today (UTC/Local day)."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count FROM whatsapp_posted_jobs
                WHERE date(posted_at) = date('now')
            """)
            row = cursor.fetchone()
            return row["count"] if row else 0

    def can_post_to_whatsapp_today(self, max_daily: int = 20) -> bool:
        """Verify that WhatsApp daily posting limit (max 20) has not been exceeded."""
        today_count = self.get_whatsapp_today_posts_count()
        return today_count < max_daily


# Global singleton instance
db = Database()
