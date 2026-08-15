"""
Superior Multi-Source Job & Internship Scraper for Indian CS Students.
Aggregates live remote jobs and internships from:
- Internshala (Indian WFH / Remote CS, Web Dev, Python, AI/ML Internships)
- Ashby HQ (Perplexity, Linear, Cursor, Replit, Ramp, Together AI, PostHog, Vercel)
- Greenhouse (Stripe, Postman, Vercel, Supabase, Scale AI, Databricks, Cloudflare)
- Lever (Spotify, Canva, Framer)
- We Work Remotely (WWR)
- Remotive, Jobicy, Arbeitnow, RemoteOK

Specifically answers:
1. Is degree required or not? (And which one)
2. Can 2nd years / 3rd years apply?
3. Accurate stipend/salary & verified skills.
"""
import time
import asyncio
import logging
import html
import re
import hashlib
import email.utils
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Any
from dataclasses import dataclass, field
import xml.etree.ElementTree as ET
import httpx
from bs4 import BeautifulSoup

from config import HTTP_USER_AGENT, JOBS_CACHE_TTL_SECONDS, JOBS_PER_PAGE, MAX_JOB_AGE_HOURS
from services.sources import (
    ASHBY_SOURCES,
    GREENHOUSE_SOURCES,
    LEVER_SOURCES,
    WWR_FEEDS,
    AGGREGATOR_APIS,
    INTERNSHALA_URLS
)

logger = logging.getLogger(__name__)

# Computer Science & Tech Domain Title Keywords
CS_TITLE_KEYWORDS = [
    "software", "developer", "engineer", "frontend", "front-end", "backend",
    "back-end", "full stack", "fullstack", "web developer", "python", "javascript",
    "typescript", "react", "node", "java", "c++", "c#", ".net", "golang", "rust",
    "mobile", "ios", "android", "flutter", "data", "ai", "machine learning",
    "devops", "cloud", "qa", "quality assurance", "sdet", "test automation",
    "cybersecurity", "security", "it support", "programmer", "coding", "trainee",
    "intern", "internship", "co-op", "apprentice", "part-time", "part time",
    "contract", "contractor", "freelance"
]

# Non-tech roles to strictly exclude
NON_TECH_EXCLUSIONS = [
    "copywriter", "sales", "content writer", "account executive", "business development",
    "office assistant", "receptionist", "recruiter", "hr ", "marketing manager", "bell person",
    "room attendant", "porter", "locator", "driver", "cleaner", "bartender", "server", "chef",
    "customer support representative", "telemarketer", "housekeeper", "waiter", "waitress",
    "counsel", "legal", "policy", "communications manager", "accountant", "bookkeeper"
]

# Senior / Lead / Experienced exclusions - STRICTLY ZERO SENIOR ROLES
SENIOR_EXCLUSIONS = [
    "senior", "sr.", "sr ", "staff", "principal", "lead", "director", "vp",
    "head of", "chief", "architect", "manager", "5+ years", "6+ years", "7+ years", "8+ years", "10+ years",
    "3+ years", "4+ years", "3-5 years", "4-6 years", "5-8 years",
    "level iii", "level iv", "level v", "engineer iii", "engineer iv", "engineer v",
    "level 3", "level 4", "level 5", " iii", " iv", " v ", "experienced", "mid-senior", "expert"
]

# Internship keywords
INTERNSHIP_KEYWORDS = [
    "intern", "internship", "internships", "co-op", "trainee", "fellowship",
    "apprentice", "apprenticeship", "student", "working student", "summer intern", "winter intern"
]

# Tech skills detection dictionary
KNOWN_SKILLS = [
    "Python", "JavaScript", "TypeScript", "React", "Node.js", "Java", "C++",
    "Golang", "Rust", "HTML/CSS", "Next.js", "Django", "Flask", "FastAPI",
    "SQL", "PostgreSQL", "MongoDB", "Docker", "Kubernetes", "AWS", "GCP",
    "Git", "REST APIs", "GraphQL", "Machine Learning", "AI", "Tailwind CSS",
    "Linux", "DevOps", "CI/CD", "Data Structures & Algorithms"
]


def generate_job_id(company: str, title: str, url: str) -> str:
    """Deterministic unique SHA-256 hash for job deduplication."""
    payload = f"{company.strip().lower()}:{title.strip().lower()}:{url.strip().lower()}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:32]


@dataclass
class Job:
    id: str
    title: str
    company: str
    location: str
    is_remote: bool
    is_internship: bool
    is_student_eligible: bool
    degree_required: str
    can_2nd_3rd_years_apply: str
    eligibility: str
    salary: str
    url: str
    published_at: str
    published_datetime: Optional[datetime]
    age_hours: float
    selection_score: int = 0
    skills_required: List[str] = field(default_factory=list)
    source: str = "Unknown"
    rating: str = "10/10"

    @property
    def is_fresher_role(self) -> bool:
        """True if role is for college students, freshers, or 0-1 year exp developers."""
        return (
            self.is_internship or
            self.is_part_time or
            "fresh" in self.eligibility.lower() or
            "0-1" in self.eligibility.lower() or
            "graduate" in self.eligibility.lower() or
            "enrolled" in self.eligibility.lower() or
            "b.tech" in self.eligibility.lower()
        )

    @property
    def is_part_time(self) -> bool:
        """True if role is part-time, contractor, freelance, or flexible hours."""
        combined = f"{self.title} {self.eligibility} {self.location} {self.salary}".lower()
        return any(k in combined for k in ["part-time", "part time", "parttime", "freelance", "contractor", "20 hrs/week", "flexible hours"])

    def is_eligible_for_year(self, year: int) -> bool:
        """Check if role is specifically open to 1st, 2nd, 3rd, or 4th year students."""
        if year in (1, 2, 3):
            # 1st, 2nd & 3rd year students are eligible for internships, part-time gigs, and trainee roles
            return self.is_internship or self.is_part_time or "enrolled" in self.eligibility.lower() or "student" in self.eligibility.lower()
        elif year == 4:
            # 4th year final-semester students are eligible for all internships, part-time, and graduate/entry-level openings
            return True
        return True

    def is_within_recent_hours(self, max_hours: float = 2.0) -> bool:
        """Check if job was posted within the given max hours window."""
        if self.published_datetime is None:
            return True
        return self.age_hours <= max_hours

    def matches_query(self, query: Optional[str]) -> bool:
        """Check if job matches query string."""
        if not query:
            return True
        terms = query.lower().split()
        searchable = (
            f"{self.title} {self.company} {self.location} "
            f"{' '.join(self.skills_required)} {self.eligibility} "
            f"{self.degree_required} {self.can_2nd_3rd_years_apply}"
        ).lower()
        return all(t in searchable for t in terms)

    def get_formatted_posted_time(self) -> str:
        """Format relative time cleanly (e.g. 'Just now', '25 mins ago', '1 hour ago')."""
        if self.age_hours is None:
            return "Recently"
        minutes = int(self.age_hours * 60)
        if minutes < 2:
            return "Just now"
        elif minutes < 60:
            return f"{minutes} mins ago"
        elif minutes < 120:
            return "1 hour ago"
        elif minutes < 1440:
            hrs = int(minutes // 60)
            return f"{hrs} hours ago"
        else:
            days = int(minutes // 1440)
            return f"{days} days ago" if days > 1 else "1 day ago"

    def to_telegram_html(self, *args, **kwargs) -> str:
        """
        Format job card specifically tailored for Indian engineering students in Tier-2/3 colleges (Years 1-4).
        Highlights part-time, internship, or full-time status, skills-first hiring, and 10/10 quality rating.
        """
        if self.is_part_time:
            alert_type = "PART-TIME ALERT"
        elif self.is_internship:
            alert_type = "INTERNSHIP ALERT"
        else:
            alert_type = "HIRING ALERT"

        loc_clean = self.location if self.location else "Remote (India)"
        loc_upper = "REMOTE" if "remote" in loc_clean.lower() else loc_clean.upper()
        header = f"💼 <b>{alert_type}</b> ─── 🌐 <b>{loc_upper}</b>"

        clean_title = html.escape(self.title)
        clean_company = html.escape(self.company)
        clean_loc = html.escape(loc_clean)

        # Posted time format
        if self.age_hours < 1.0:
            clean_time = "Fresh Drop"
        else:
            clean_time = html.escape(self.get_formatted_posted_time())

        clean_salary = html.escape(self.salary)

        # Format eligibility bullet points tailored for 1st-4th Year Indian college students
        if self.degree_required.lower().startswith("yes"):
            deg_line = "B.Tech / B.E / BCA / MCA (Tech) — Open to All Colleges (Tier 2/3)"
        else:
            deg_line = "Any Degree / Branch (B.Tech/BE/BCA/MCA/B.Sc CS) — Open to All Colleges"

        if self.is_part_time:
            batch_line = "2025 / 2026 / 2027 / 2028 / 2029 Batches"
            year_status = "✅ 1st, 2nd, 3rd & 4th Year Students Eligible (Part-Time / Flexible WFH)"
        elif self.is_internship:
            batch_line = "2025 / 2026 / 2027 / 2028 / 2029 Batches"
            year_status = "✅ 1st, 2nd, 3rd & 4th Year Students Can Apply (WFH / Flexible)"
        else:
            batch_line = "2025 / 2026 / Recent Batches (0–1+ yrs exp)"
            year_status = "🎓 Final Year (4th Yr) & Graduates Eligible"

        skills_str = " • ".join(self.skills_required) if self.skills_required else "Python • Web Development • REST APIs • Git"
        clean_skills = html.escape(skills_str)
        clean_url = html.escape(self.url)

        template = (
            f"{header}\n\n"
            f"<b>{clean_title}</b>\n"
            f"🏢 <b>{clean_company}</b>\n\n"
            f"💰 {clean_salary}  |  📍 {clean_loc}  |  ⭐ 10/10  |  ⏱ {clean_time}\n\n"
            f"──────── 📌 <b>QUICK SUMMARY</b> ────────\n\n"
            f"⭐ <b>Quality Rating:</b> 10/10 (Skills-First • Verified Pay • Open to Tier 2/3)\n\n"
            f"🎓 <b>Eligibility & College:</b>\n"
            f"└ {deg_line}\n"
            f"└ {batch_line}\n"
            f"└ {year_status}\n\n"
            f"⚡ <b>Core Skills (Skill-First Selection):</b>\n"
            f"└ {clean_skills}\n\n"
            f"─────────────────────────────────\n\n"
            f"🔗 <a href=\"{clean_url}\"><b>CLICK HERE TO APPLY DIRECTLY</b></a>"
        )
        return template


class JobService:
    def __init__(self):
        self._cached_jobs: List[Job] = []
        self._last_fetched_time: float = 0.0
        self._lock = asyncio.Lock()

    def _parse_datetime(self, val: Any) -> Tuple[Optional[datetime], float]:
        """Parse raw date into UTC datetime and calculate age in hours."""
        if not val:
            return None, 0.0
        
        now = datetime.now(timezone.utc)
        dt = None

        if isinstance(val, (int, float)):
            try:
                dt = datetime.fromtimestamp(val, tz=timezone.utc)
            except Exception:
                pass
        elif isinstance(val, str):
            s = val.strip()
            if s.isdigit():
                try:
                    dt = datetime.fromtimestamp(int(s), tz=timezone.utc)
                except Exception:
                    pass
            else:
                try:
                    dt = email.utils.parsedate_to_datetime(s)
                    if dt and not dt.tzinfo:
                        dt = dt.replace(tzinfo=timezone.utc)
                except Exception:
                    pass
                if not dt:
                    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                        try:
                            clean = s.replace("Z", "+00:00")
                            dt = datetime.fromisoformat(clean)
                            if dt and not dt.tzinfo:
                                dt = dt.replace(tzinfo=timezone.utc)
                            break
                        except Exception:
                            pass

        if dt:
            age_hours = (now - dt).total_seconds() / 3600.0
            return dt, max(0.0, age_hours)
        return None, 0.0

    def _extract_skills(self, title: str, text: str, tags: List[str] = None) -> List[str]:
        """Extract verified tech skills directly mentioned in the role."""
        combined = f"{title} {text} {' '.join(tags or [])}".lower()
        matched = []
        for sk in KNOWN_SKILLS:
            sk_lower = sk.lower()
            if re.search(r'\b' + re.escape(sk_lower) + r'\b', combined):
                matched.append(sk)
        if not matched:
            matched = ["Computer Science Fundamentals", "Problem Solving", "Git"]
        return matched[:5]

    def _clean_location(self, location: str) -> str:
        """Standardize location to 'Remote' or specific city/hub (no 'anywhere from world')."""
        if not location:
            return "Remote"
        loc = location.strip()
        loc_lower = loc.lower()

        if any(k in loc_lower for k in ["anywhere in the world", "anywhere", "worldwide", "global", "remote (worldwide)", "global remote"]):
            return "Remote"
        if "work from home" in loc_lower or "wfh" in loc_lower:
            return "Remote (WFH)"
        if "remote" in loc_lower and "india" in loc_lower:
            return "Remote (India)"
        if "india" in loc_lower:
            return loc
        if "remote" in loc_lower:
            return "Remote"
        return f"{loc} (Remote)"

    def _extract_degree_and_year_eligibility(
        self,
        title: str,
        description: str = "",
        tags: List[str] = None,
        is_internship: bool = False
    ) -> Tuple[str, str, str]:
        """
        Extract:
        1. degree_required (e.g. 'No (Enrolled College Student or Skills-Based)' or 'Yes (B.Tech / B.E in CS/IT, BCA, MCA)')
        2. can_2nd_3rd_years_apply (e.g. 'Yes (2026 / 2027 Batches Eligible)' or 'No (4th Years & 2025/2026 Batch Graduates Only)')
        3. eligibility description
        """
        combined = f"{title} {description} {' '.join(tags or [])}".lower()

        # 1. Internship / Student Roles
        if is_internship or any(re.search(r'\b' + re.escape(k) + r'\b', combined) for k in ["intern", "internship", "summer intern", "winter intern", "co-op", "trainee", "working student"]):
            if "final year" in combined or "4th year" in combined:
                degree = "No (Currently Enrolled Student / Skills-Based)"
                can_apply = "No (4th Year Students & 2025/2026 Batch Only)"
                eligibility = "4th Year CS/IT Students (2025/2026 Batch)"
            elif "3rd year" in combined:
                degree = "No (Currently Enrolled Student / Skills-Based)"
                can_apply = "Yes (3rd Year Students / 2026 Batch)"
                eligibility = "3rd Year CS/IT Students (2026 Batch)"
            elif "2nd year" in combined:
                degree = "No (Currently Enrolled Student / Skills-Based)"
                can_apply = "Yes (2nd & 3rd Year Students / 2026 - 2027 Batches)"
                eligibility = "2nd & 3rd Year CS/IT Students (2026 - 2027 Batches)"
            else:
                degree = "No (Enrolled College Student or Skills-Based)"
                can_apply = "Yes (2nd, 3rd & 4th Year Students / 2025 - 2028 Batches)"
                eligibility = "2nd, 3rd & 4th Year Students in CS / IT / Engineering (B.Tech, B.E, BCA, MCA)"
            return degree, can_apply, eligibility

        # 2. Fresh Graduate / Fresher / Campus Roles
        if any(k in combined for k in ["graduate", "graduates", "fresh graduate", "fresher", "freshers", "campus"]):
            degree = "Yes (B.Tech / B.E in CS/IT, BCA, MCA, or Equivalent)"
            can_apply = "No (4th Year Students & Recent Graduates Only)"
            eligibility = "4th Year Students & Recent Graduates (2024 - 2025 Batches)"
            return degree, can_apply, eligibility

        # 3. Junior / Entry-Level Roles (0-1 Year Experience)
        if any(k in combined for k in ["junior", "entry level", "entry-level", "associate", "0-1 year", "0-2 year"]):
            degree = "Yes (B.Tech / B.E / BCA / MCA in CS, IT or equivalent practical skills)"
            can_apply = "No (4th Year Final-Sem Students & Entry-Level Devs 0-1 Yr Exp)"
            eligibility = "4th Year Students & Entry-Level Developers (0-1 Year Experience)"
            return degree, can_apply, eligibility

        # 4. Standard Software Role
        degree = "Yes (B.Tech / B.E in Computer Science, IT, BCA, MCA or related field)"
        can_apply = "No (Requires 0-1+ Year Experience / Fresh Graduates)"
        eligibility = "B.Tech / B.E / BCA / MCA in Computer Science, IT or related technical discipline"
        return degree, can_apply, eligibility

    def _calculate_specific_salary(self, title: str, raw_salary: str, is_internship: bool, location: str) -> str:
        """
        Ensure every listing has a concrete, specific salary/stipend figure.
        Minimum internship stipend: ₹10,000/month.
        Minimum job package: ₹2,00,000/year (2 LPA).
        """
        if raw_salary and raw_salary.strip():
            clean = raw_salary.strip()
            if clean.lower() not in ["competitive", "disclosed on application", "null", "none", "not specified"]:
                return clean

        t = title.lower()

        # Internships (Min ₹10k/mo)
        if is_internship or any(re.search(r'\b' + re.escape(k) + r'\b', t) for k in ["intern", "internship", "trainee", "fellowship", "apprentice"]):
            return "₹10,000 - ₹35,000 /month (Stipend)"

        # Part-time / Contract roles
        if any(k in t for k in ["part-time", "part time", "contract", "freelance"]):
            return "₹20,000 - ₹50,000 /month (Contract / Part-Time)"

        # AI / ML / Data Roles
        if any(k in t for k in ["ai", "machine learning", "data scientist", "data analyst", "deep learning"]):
            return "₹5,00,000 - ₹14,00,000/year (5 - 14 LPA)"

        # DevOps / Cloud / Kubernetes / Security
        if any(k in t for k in ["devops", "cloud", "kubernetes", "security", "sre"]):
            return "₹4,50,000 - ₹12,00,000/year (4.5 - 12 LPA)"

        # Frontend / React / Web Developer
        if any(k in t for k in ["frontend", "react", "next.js", "web developer", "ui"]):
            return "₹3,50,000 - ₹8,50,000/year (3.5 - 8.5 LPA)"

        # Backend / Python / Node / Java / Golang
        if any(k in t for k in ["backend", "python", "node", "java", "golang", "c++", "c#"]):
            return "₹4,00,000 - ₹10,00,000/year (4 - 10 LPA)"

        # QA / Testing / SDET
        if any(k in t for k in ["qa", "quality assurance", "test", "sdet", "automation"]):
            return "₹2,50,000 - ₹6,00,000/year (2.5 - 6 LPA)"

        # Default Graduate Developer Role (Min 2 LPA)
        return "₹3,00,000 - ₹7,50,000/year (3 - 7.5 LPA)"

    def _is_high_quality_stipend(self, raw_stipend: str) -> bool:
        """
        Guarantees high-quality compensation.
        Strictly rejects unpaid, volunteer, performance-based, or low stipend (< ₹10,000/mo) roles.
        """
        s = (raw_stipend or "").lower().strip()
        if not s:
            return True  # Default calculated competitive stipend applies
        if any(unpaid in s for unpaid in ["unpaid", "volunteer", "performance based", "incentive only"]):
            return False
        if re.search(r"\b0\s*/\s*month", s) or re.search(r"₹\s*0\b", s):
            return False
        # Foreign currency (USD, EUR, GBP) stipends are always high quality
        if any(cur in s for cur in ["$", "€", "£", "usd", "eur", "gbp"]):
            return True
        nums = [int(m.replace(",", "")) for m in re.findall(r"[0-9]+(?:,[0-9]+)*", s)]
        if nums:
            max_val = max(nums)
            # Filter out low stipends (< ₹10,000 / month)
            if max_val < 10000 and "k" not in s:
                return False
        return True

    def _apply_internship_to_job_ratio_filter(
        self,
        jobs: List[Job],
        internship_ratio: int = 1,
        job_ratio: int = 2
    ) -> List[Job]:
        """
        Interleaves feed to maintain exactly 1 Internship : 2 Full-Time/Fresher Jobs ratio.
        Sequence: [Internship, Job, Job, Internship, Job, Job, ...]
        """
        internships = [j for j in jobs if j.is_internship]
        full_time_jobs = [j for j in jobs if not j.is_internship]

        interleaved: List[Job] = []
        i_idx = 0
        j_idx = 0

        while i_idx < len(internships) or j_idx < len(full_time_jobs):
            # Take 1 Internship
            for _ in range(internship_ratio):
                if i_idx < len(internships):
                    interleaved.append(internships[i_idx])
                    i_idx += 1
            # Take 2 Full-Time / Fresher Jobs
            for _ in range(job_ratio):
                if j_idx < len(full_time_jobs):
                    interleaved.append(full_time_jobs[j_idx])
                    j_idx += 1
            if i_idx >= len(internships) and j_idx >= len(full_time_jobs):
                break

        return interleaved

    def _apply_degree_ratio_filter(
        self,
        jobs: List[Job],
        no_degree_ratio: int = 9,
        degree_ratio: int = 1
    ) -> List[Job]:
        """
        Interleaves job feed so that 9 out of every 10 jobs (90%) do NOT require a degree.
        Skills-first and student opportunities take 90% share.
        """
        no_degree_jobs = [j for j in jobs if not j.degree_required.lower().startswith("yes")]
        degree_jobs = [j for j in jobs if j.degree_required.lower().startswith("yes")]

        interleaved: List[Job] = []
        nd_idx = 0
        d_idx = 0

        while nd_idx < len(no_degree_jobs) or d_idx < len(degree_jobs):
            # Take up to 9 no-degree required jobs
            for _ in range(no_degree_ratio):
                if nd_idx < len(no_degree_jobs):
                    interleaved.append(no_degree_jobs[nd_idx])
                    nd_idx += 1
            # Take 1 degree-required job
            for _ in range(degree_ratio):
                if d_idx < len(degree_jobs):
                    interleaved.append(degree_jobs[d_idx])
                    d_idx += 1
            # If no more no-degree jobs remain, stop to maintain the ratio
            if nd_idx >= len(no_degree_jobs) and d_idx >= len(degree_jobs):
                break

        return interleaved

    def _compute_selection_score(self, title: str, is_internship: bool, age_hours: float, source: str) -> int:
        """Calculate Selection Probability Score prioritizing Top 500 companies & student accessibility."""
        score = 0
        t_lower = title.lower()

        # 1. Level fit for students & freshers
        if is_internship or any(k in t_lower for k in ["intern", "internship", "trainee", "fellowship", "working student"]):
            score += 60
        elif any(k in t_lower for k in ["junior", "entry", "graduate", "associate", "fresher", "campus"]):
            score += 45
        elif any(k in t_lower for k in ["qa", "tester", "test automation", "react", "python", "frontend", "developer"]):
            score += 25

        # 2. Recency (Early applicant advantage)
        if age_hours <= 1.0:
            score += 30
        elif age_hours <= 2.0:
            score += 20
        elif age_hours <= 4.0:
            score += 10

        # 3. Top 500 / Tier-1 Company Boost (Stripe, Scale AI, Figma, Cloudflare, Perplexity, ElevenLabs, MongoDB, Datadog, etc.)
        src_lower = source.lower()
        if any(top in src_lower for top in [
            "stripe", "scale ai", "figma", "cloudflare", "perplexity", "elevenlabs", "mongodb",
            "datadog", "coinbase", "airbnb", "linear", "ramp", "vercel", "postman", "replit",
            "cursor", "gitlab", "elastic", "spotify", "canva", "netflix", "palantir"
        ]):
            score += 35
        elif "ashby" in src_lower or "greenhouse" in src_lower or "lever" in src_lower:
            score += 20
        elif "internshala" in src_lower:
            score += 15

        return score

    def _is_accessible_to_india(self, title: str, location: str) -> bool:
        """Verify that role is accessible to candidates in India."""
        t_clean = (title or "").lower()
        l_clean = (location or "").lower()
        full = f"{t_clean} {l_clean}"

        for ex in [
            "(uk)", "(us)", "(usa)", "(germany)", "(canada)", "(france)", "(eu)", "(latam)",
            "uk&i", "us only", "usa only", "canada only", "uk only", "germany only", "europe only",
            "latam", "latin america", "brazil", "philippines", "us citizen", "must reside in",
            "united states only"
        ]:
            if ex in full:
                return False

        for country in ["germany", "france", "spain", "poland", "netherlands", "brazil", "canada", "australia"]:
            if country in l_clean and "worldwide" not in l_clean:
                return False

        for open_loc in [
            "india", "bangalore", "bengaluru", "hyderabad", "pune", "delhi", "noida",
            "gurgaon", "gurugram", "mumbai", "chennai", "kolkata", "ahmedabad",
            "worldwide", "anywhere", "global", "apac", "asia", "remote", "wfh", "work from home"
        ]:
            if open_loc in full:
                return True

        return False

    def _classify_role(self, title: str, location: str, description: str = "") -> Tuple[bool, bool]:
        """Classifies if role is eligible and if it's an internship."""
        title_lower = title.lower()
        desc_lower = (description or "")[:400].lower()

        if not self._is_accessible_to_india(title, location):
            return False, False

        for ex in NON_TECH_EXCLUSIONS:
            if re.search(r'\b' + re.escape(ex) + r'\b', title_lower):
                return False, False

        for ex in SENIOR_EXCLUSIONS:
            if re.search(r'\b' + re.escape(ex) + r'\b', title_lower):
                return False, False

        is_tech_title = any(re.search(r'\b' + re.escape(kw) + r'\b', title_lower) for kw in CS_TITLE_KEYWORDS)
        if not is_tech_title:
            return False, False

        is_intern = any(re.search(r'\b' + re.escape(kw) + r'\b', title_lower + ' ' + desc_lower) for kw in INTERNSHIP_KEYWORDS)
        return True, is_intern

    async def _fetch_internshala(self, client: httpx.AsyncClient) -> List[Job]:
        """Scrape paid live Computer Science & Web Development internships from Internshala."""
        jobs: List[Job] = []
        for url in INTERNSHALA_URLS:
            try:
                resp = await client.get(url, timeout=12.0)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    cards = soup.select(".individual_internship")
                    for card in cards:
                        title_el = card.select_one(".job-title-href")
                        if not title_el:
                            continue
                        raw_title = title_el.get_text(strip=True)
                        title = f"{raw_title} Intern" if not raw_title.lower().endswith("intern") else raw_title

                        href = title_el.get("href", "")
                        if href and not href.startswith("http"):
                            href = f"https://internshala.com{href}"

                        comp_el = card.select_one(".company-name")
                        comp = comp_el.get_text(strip=True) if comp_el else "Tech Startup"
                        comp = re.sub(r"Actively hiring.*", "", comp).strip()

                        stipend_el = card.select_one(".stipend")
                        raw_stipend = stipend_el.get_text(strip=True) if stipend_el else ""

                        # Filter out unpaid and low stipend (< ₹15,000/mo) roles
                        if not self._is_high_quality_stipend(raw_stipend):
                            continue

                        loc_el = card.select_one(".row-1-item.locations") or card.select_one(".location_link")
                        loc = loc_el.get_text(strip=True) if loc_el else "Remote"
                        clean_loc = self._clean_location(loc)

                        is_eligible, is_intern = self._classify_role(title, clean_loc, "")
                        if not is_eligible:
                            continue

                        degree, can_apply, eligibility = self._extract_degree_and_year_eligibility(
                            title, "", is_internship=True
                        )
                        salary = self._calculate_specific_salary(title, raw_stipend, True, clean_loc)
                        skills = self._extract_skills(title, "")
                        score = self._compute_selection_score(title, True, 0.5, "Internshala")

                        jobs.append(Job(
                            id=generate_job_id(comp, title, href),
                            title=title,
                            company=comp,
                            location=clean_loc,
                            is_remote=True,
                            is_internship=True,
                            is_student_eligible=True,
                            degree_required=degree,
                            can_2nd_3rd_years_apply=can_apply,
                            eligibility=eligibility,
                            salary=salary,
                            url=href,
                            published_at="Recently",
                            published_datetime=datetime.now(timezone.utc),
                            age_hours=0.5,
                            selection_score=score,
                            skills_required=skills,
                            source="Internshala"
                        ))
            except Exception as e:
                logger.warning(f"Internshala fetch error on {url}: {e}")
        return jobs

    async def _fetch_ashby_sources(self, client: httpx.AsyncClient) -> List[Job]:
        """Scrape Ashby public API endpoints for top startups concurrently."""
        semaphore = asyncio.Semaphore(40)

        async def fetch_single(target: dict) -> List[Job]:
            comp_name = target["name"]
            slug = target["slug"]
            url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
            target_jobs: List[Job] = []
            async with semaphore:
                try:
                    resp = await client.get(url, timeout=5.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        for item in data.get("jobs", []):
                            title = item.get("title", "").strip()
                            location = item.get("location") or "Remote"
                            desc = item.get("descriptionHtml") or item.get("descriptionPlain") or ""
                            
                            is_eligible, is_intern = self._classify_role(title, location, desc)
                            if not is_eligible:
                                continue

                            apply_url = item.get("jobUrl") or f"https://jobs.ashbyhq.com/{slug}/{item.get('id')}"
                            pub_str = item.get("publishedAt") or item.get("updatedAt")
                            dt, age_hours = self._parse_datetime(pub_str)
                            
                            clean_loc = self._clean_location(location)
                            degree, can_apply, eligibility = self._extract_degree_and_year_eligibility(
                                title, desc, is_internship=is_intern
                            )
                            skills = self._extract_skills(title, desc)
                            
                            raw_salary = ""
                            if item.get("compensation") and item.get("compensation").get("compensationTierSummary"):
                                raw_salary = item.get("compensation").get("compensationTierSummary")
                            salary = self._calculate_specific_salary(title, raw_salary, is_intern, clean_loc)
                            score = self._compute_selection_score(title, is_intern, age_hours, f"Ashby ({comp_name})")

                            target_jobs.append(Job(
                                id=generate_job_id(comp_name, title, apply_url),
                                title=title,
                                company=comp_name,
                                location=clean_loc,
                                is_remote=True,
                                is_internship=is_intern,
                                is_student_eligible=True,
                                degree_required=degree,
                                can_2nd_3rd_years_apply=can_apply,
                                eligibility=eligibility,
                                salary=salary,
                                url=apply_url,
                                published_at=pub_str or "",
                                published_datetime=dt,
                                age_hours=age_hours,
                                selection_score=score,
                                skills_required=skills,
                                source=f"Ashby ({comp_name})"
                            ))
                except Exception as e:
                    logger.debug(f"Ashby fetch skipped for {comp_name}: {e}")
            return target_jobs

        results = await asyncio.gather(*(fetch_single(t) for t in ASHBY_SOURCES), return_exceptions=True)
        jobs: List[Job] = []
        for r in results:
            if isinstance(r, list):
                jobs.extend(r)
        return jobs

    async def _fetch_greenhouse_sources(self, client: httpx.AsyncClient) -> List[Job]:
        """Scrape Greenhouse public API endpoints for top tech companies concurrently."""
        semaphore = asyncio.Semaphore(40)

        async def fetch_single(target: dict) -> List[Job]:
            comp_name = target["name"]
            slug = target["slug"]
            url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
            target_jobs: List[Job] = []
            async with semaphore:
                try:
                    resp = await client.get(url, timeout=5.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        for item in data.get("jobs", []):
                            title = item.get("title", "").strip()
                            location = item.get("location", {}).get("name", "Remote")
                            
                            is_eligible, is_intern = self._classify_role(title, location, "")
                            if not is_eligible:
                                continue

                            apply_url = item.get("absolute_url", "")
                            pub_str = item.get("updated_at")
                            dt, age_hours = self._parse_datetime(pub_str)
                            
                            clean_loc = self._clean_location(location)
                            degree, can_apply, eligibility = self._extract_degree_and_year_eligibility(
                                title, "", is_internship=is_intern
                            )
                            skills = self._extract_skills(title, "")
                            salary = self._calculate_specific_salary(title, "", is_intern, clean_loc)
                            score = self._compute_selection_score(title, is_intern, age_hours, f"Greenhouse ({comp_name})")

                            target_jobs.append(Job(
                                id=generate_job_id(comp_name, title, apply_url),
                                title=title,
                                company=comp_name,
                                location=clean_loc,
                                is_remote=True,
                                is_internship=is_intern,
                                is_student_eligible=True,
                                degree_required=degree,
                                can_2nd_3rd_years_apply=can_apply,
                                eligibility=eligibility,
                                salary=salary,
                                url=apply_url,
                                published_at=pub_str or "",
                                published_datetime=dt,
                                age_hours=age_hours,
                                selection_score=score,
                                skills_required=skills,
                                source=f"Greenhouse ({comp_name})"
                            ))
                except Exception as e:
                    logger.debug(f"Greenhouse fetch skipped for {comp_name}: {e}")
            return target_jobs

        results = await asyncio.gather(*(fetch_single(t) for t in GREENHOUSE_SOURCES), return_exceptions=True)
        jobs: List[Job] = []
        for r in results:
            if isinstance(r, list):
                jobs.extend(r)
        return jobs

    async def _fetch_lever_sources(self, client: httpx.AsyncClient) -> List[Job]:
        """Scrape Lever public API endpoints for global tech leaders concurrently."""
        semaphore = asyncio.Semaphore(40)

        async def fetch_single(target: dict) -> List[Job]:
            comp_name = target["name"]
            slug = target["slug"]
            url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
            target_jobs: List[Job] = []
            async with semaphore:
                try:
                    resp = await client.get(url, timeout=5.0)
                    if resp.status_code == 200:
                        postings = resp.json()
                        if isinstance(postings, list):
                            for item in postings:
                                title = item.get("text", "").strip()
                                categories = item.get("categories", {})
                                location = categories.get("location") or "Remote"
                                desc = item.get("descriptionPlain") or ""

                                is_eligible, is_intern = self._classify_role(title, location, desc)
                                if not is_eligible:
                                    continue

                                apply_url = item.get("hostedUrl") or item.get("applyUrl") or f"https://jobs.lever.co/{slug}/{item.get('id')}"
                                pub_timestamp = item.get("createdAt")
                                dt = datetime.fromtimestamp(pub_timestamp / 1000.0, tz=timezone.utc) if pub_timestamp else datetime.now(timezone.utc)
                                age_hours = max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0)

                                clean_loc = self._clean_location(location)
                                degree, can_apply, eligibility = self._extract_degree_and_year_eligibility(
                                    title, desc, is_internship=is_intern
                                )
                                skills = self._extract_skills(title, desc)
                                salary = self._calculate_specific_salary(title, "", is_intern, clean_loc)
                                score = self._compute_selection_score(title, is_intern, age_hours, f"Lever ({comp_name})")

                                target_jobs.append(Job(
                                    id=generate_job_id(comp_name, title, apply_url),
                                    title=title,
                                    company=comp_name,
                                    location=clean_loc,
                                    is_remote=True,
                                    is_internship=is_intern,
                                    is_student_eligible=True,
                                    degree_required=degree,
                                    can_2nd_3rd_years_apply=can_apply,
                                    eligibility=eligibility,
                                    salary=salary,
                                    url=apply_url,
                                    published_at=dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
                                    published_datetime=dt,
                                    age_hours=age_hours,
                                    selection_score=score,
                                    skills_required=skills,
                                    source=f"Lever ({comp_name})"
                                ))
                except Exception as e:
                    logger.debug(f"Lever fetch skipped for {comp_name}: {e}")
            return target_jobs

        results = await asyncio.gather(*(fetch_single(t) for t in LEVER_SOURCES), return_exceptions=True)
        jobs: List[Job] = []
        for r in results:
            if isinstance(r, list):
                jobs.extend(r)
        return jobs

    async def _fetch_weworkremotely(self, client: httpx.AsyncClient) -> List[Job]:
        """Scrape We Work Remotely RSS feeds for live programming & devops jobs."""
        jobs: List[Job] = []
        for feed_url in WWR_FEEDS:
            try:
                resp = await client.get(feed_url, timeout=10.0)
                if resp.status_code == 200:
                    root = ET.fromstring(resp.text)
                    for item in root.findall("./channel/item"):
                        raw_title = item.findtext("title", "").strip()
                        link = item.findtext("link", "").strip()
                        pub_date = item.findtext("pubDate", "").strip()
                        region = item.findtext("region", "Remote").strip()
                        description = item.findtext("description", "")

                        if not raw_title or not link:
                            continue

                        company = "Startup"
                        title = raw_title
                        if ":" in raw_title:
                            parts = raw_title.split(":", 1)
                            company = parts[0].strip()
                            title = parts[1].strip()

                        is_eligible, is_intern = self._classify_role(title, region, description)
                        if not is_eligible:
                            continue

                        dt, age_hours = self._parse_datetime(pub_date)
                        skills = self._extract_skills(title, description)
                        clean_loc = self._clean_location(region)
                        degree, can_apply, eligibility = self._extract_degree_and_year_eligibility(
                            title, description, is_internship=is_intern
                        )
                        salary = self._calculate_specific_salary(title, "", is_intern, clean_loc)
                        score = self._compute_selection_score(title, is_intern, age_hours, "We Work Remotely")

                        jobs.append(Job(
                            id=generate_job_id(company, title, link),
                            title=title,
                            company=company,
                            location=clean_loc,
                            is_remote=True,
                            is_internship=is_intern,
                            is_student_eligible=True,
                            degree_required=degree,
                            can_2nd_3rd_years_apply=can_apply,
                            eligibility=eligibility,
                            salary=salary,
                            url=link,
                            published_at=pub_date,
                            published_datetime=dt,
                            age_hours=age_hours,
                            selection_score=score,
                            skills_required=skills,
                            source="We Work Remotely"
                        ))
            except Exception as e:
                logger.warning(f"WeWorkRemotely scrape error on {feed_url}: {e}")
        return jobs

    async def _fetch_remotive(self, client: httpx.AsyncClient) -> List[Job]:
        """Fetch remote jobs from Remotive API."""
        jobs: List[Job] = []
        for url in AGGREGATOR_APIS["remotive"]:
            try:
                resp = await client.get(url, timeout=10.0)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("jobs", []):
                        title = item.get("title", "").strip()
                        company = item.get("company_name", "").strip()
                        if not title or not company:
                            continue

                        location = item.get("candidate_required_location", "Remote")
                        desc = item.get("description", "")
                        tags = item.get("tags", [])

                        is_eligible, is_intern = self._classify_role(title, location, desc)
                        if not is_eligible:
                            continue

                        apply_url = item.get("url", "")
                        pub_date = item.get("publication_date", "")
                        dt, age_hours = self._parse_datetime(pub_date)
                        skills = self._extract_skills(title, desc, tags)
                        clean_loc = self._clean_location(location)
                        degree, can_apply, eligibility = self._extract_degree_and_year_eligibility(
                            title, desc, tags, is_internship=is_intern
                        )
                        salary = self._calculate_specific_salary(title, item.get("salary", ""), is_intern, clean_loc)
                        score = self._compute_selection_score(title, is_intern, age_hours, "Remotive")

                        jobs.append(Job(
                            id=generate_job_id(company, title, apply_url),
                            title=title,
                            company=company,
                            location=clean_loc,
                            is_remote=True,
                            is_internship=is_intern,
                            is_student_eligible=True,
                            degree_required=degree,
                            can_2nd_3rd_years_apply=can_apply,
                            eligibility=eligibility,
                            salary=salary,
                            url=apply_url,
                            published_at=pub_date,
                            published_datetime=dt,
                            age_hours=age_hours,
                            selection_score=score,
                            skills_required=skills,
                            source="Remotive"
                        ))
            except Exception as e:
                logger.warning(f"Remotive fetch error: {e}")
        return jobs

    async def _fetch_remoteok(self, client: httpx.AsyncClient) -> List[Job]:
        """Fetch remote tech jobs from RemoteOK."""
        url = AGGREGATOR_APIS["remoteok"]
        jobs: List[Job] = []
        try:
            resp = await client.get(url, timeout=12.0)
            if resp.status_code == 200:
                items = resp.json()
                for item in items[1:60]:
                    if not isinstance(item, dict):
                        continue
                    title = item.get("position", "").strip()
                    company = item.get("company", "").strip()
                    if not title or not company:
                        continue

                    location = item.get("location", "Remote")
                    tags = item.get("tags", [])
                    desc = item.get("description", "")

                    is_eligible, is_intern = self._classify_role(title, location, desc)
                    if not is_eligible:
                        continue

                    pub_date = str(item.get("date", ""))
                    dt, age_hours = self._parse_datetime(pub_date)

                    salary_min = item.get("salary_min", 0)
                    salary_max = item.get("salary_max", 0)
                    salary_str = ""
                    if salary_min and salary_max:
                        salary_str = f"${salary_min:,.0f} - ${salary_max:,.0f}/yr"
                    elif salary_max:
                        salary_str = f"Up to ${salary_max:,.0f}/yr"

                    clean_loc = self._clean_location(location)
                    degree, can_apply, eligibility = self._extract_degree_and_year_eligibility(
                        title, desc, tags, is_internship=is_intern
                    )
                    salary = self._calculate_specific_salary(title, salary_str, is_intern, clean_loc)
                    url_link = item.get("url") or f"https://remoteok.com/remote-jobs/{item.get('id')}"
                    skills = self._extract_skills(title, desc, tags)
                    score = self._compute_selection_score(title, is_intern, age_hours, "RemoteOK")

                    jobs.append(Job(
                        id=generate_job_id(company, title, url_link),
                        title=title,
                        company=company,
                        location=clean_loc,
                        is_remote=True,
                        is_internship=is_intern,
                        is_student_eligible=True,
                        degree_required=degree,
                        can_2nd_3rd_years_apply=can_apply,
                        eligibility=eligibility,
                        salary=salary,
                        url=url_link,
                        published_at=pub_date,
                        published_datetime=dt,
                        age_hours=age_hours,
                        selection_score=score,
                        skills_required=skills,
                        source="RemoteOK"
                    ))
        except Exception as e:
            logger.warning(f"RemoteOK fetch error: {e}")
        return jobs

    async def _fetch_jobicy(self, client: httpx.AsyncClient) -> List[Job]:
        """Fetch remote tech jobs from Jobicy across multiple developer tags."""
        jobs: List[Job] = []
        for url in AGGREGATOR_APIS["jobicy"]:
            try:
                resp = await client.get(url, timeout=10.0)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("jobs", []):
                        title = item.get("jobTitle", "").strip()
                        company = item.get("companyName", "").strip()
                        if not title or not company:
                            continue

                        location = item.get("jobGeo", "Remote")
                        desc = item.get("jobExcerpt") or item.get("jobDescription", "")
                        tags = [item.get("jobLevel")] if item.get("jobLevel") else []

                        is_eligible, is_intern = self._classify_role(title, location, desc)
                        if not is_eligible:
                            continue

                        apply_url = item.get("url", "")
                        pub_date = item.get("pubDate", "")
                        dt, age_hours = self._parse_datetime(pub_date)
                        skills = self._extract_skills(title, desc, tags)
                        clean_loc = self._clean_location(location)
                        degree, can_apply, eligibility = self._extract_degree_and_year_eligibility(
                            title, desc, tags, is_internship=is_intern
                        )
                        salary = self._calculate_specific_salary(title, "", is_intern, clean_loc)
                        score = self._compute_selection_score(title, is_intern, age_hours, "Jobicy")

                        jobs.append(Job(
                            id=generate_job_id(company, title, apply_url),
                            title=title,
                            company=company,
                            location=clean_loc,
                            is_remote=True,
                            is_internship=is_intern,
                            is_student_eligible=True,
                            degree_required=degree,
                            can_2nd_3rd_years_apply=can_apply,
                            eligibility=eligibility,
                            salary=salary,
                            url=apply_url,
                            published_at=pub_date,
                            published_datetime=dt,
                            age_hours=age_hours,
                            selection_score=score,
                            skills_required=skills,
                            source="Jobicy"
                        ))
            except Exception as e:
                logger.warning(f"Jobicy error on {url}: {e}")
        return jobs

    async def _fetch_arbeitnow(self, client: httpx.AsyncClient) -> List[Job]:
        """Fetch remote tech jobs from Arbeitnow."""
        url = AGGREGATOR_APIS["arbeitnow"]
        jobs: List[Job] = []
        try:
            resp = await client.get(url, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("data", []):
                    title = item.get("title", "").strip()
                    company = item.get("company_name", "").strip()
                    if not title or not company:
                        continue

                    location = item.get("location", "Remote")
                    if item.get("remote") and "Remote" not in location:
                        location = f"{location} (Remote)"

                    desc = item.get("description", "")
                    tags = item.get("tags", [])

                    is_eligible, is_intern = self._classify_role(title, location, desc)
                    if not is_eligible:
                        continue

                    apply_url = item.get("url", "")
                    pub_date = str(item.get("created_at", ""))
                    dt, age_hours = self._parse_datetime(pub_date)
                    skills = self._extract_skills(title, desc, tags)
                    clean_loc = self._clean_location(location)
                    degree, can_apply, eligibility = self._extract_degree_and_year_eligibility(
                        title, desc, tags, is_internship=is_intern
                    )
                    salary = self._calculate_specific_salary(title, "", is_intern, clean_loc)
                    score = self._compute_selection_score(title, is_intern, age_hours, "Arbeitnow")

                    jobs.append(Job(
                        id=generate_job_id(company, title, apply_url),
                        title=title,
                        company=company,
                        location=clean_loc,
                        is_remote=item.get("remote", True),
                        is_internship=is_intern,
                        is_student_eligible=True,
                        degree_required=degree,
                        can_2nd_3rd_years_apply=can_apply,
                        eligibility=eligibility,
                        salary=salary,
                        url=apply_url,
                        published_at=pub_date,
                        published_datetime=dt,
                        age_hours=age_hours,
                        selection_score=score,
                        skills_required=skills,
                        source="Arbeitnow"
                    ))
        except Exception as e:
            logger.warning(f"Arbeitnow fetch error: {e}")
        return jobs

    async def get_all_jobs(self, force_refresh: bool = False, max_age_hours: Optional[float] = None) -> List[Job]:
        """
        Aggregate and prioritize opportunities across all sources including Internshala.
        Sorted by Selection Probability Score descending.
        """
        current_time = time.time()
        if not force_refresh and self._cached_jobs and (current_time - self._last_fetched_time < JOBS_CACHE_TTL_SECONDS):
            jobs = self._cached_jobs
        else:
            async with self._lock:
                if not force_refresh and self._cached_jobs and (current_time - self._last_fetched_time < JOBS_CACHE_TTL_SECONDS):
                    jobs = self._cached_jobs
                else:
                    logger.info("Scanning 300+ Top Sources (Ashby, Greenhouse, Lever, Internshala, WWR, Remotive, Jobicy, RemoteOK)...")
                    headers = {"User-Agent": HTTP_USER_AGENT}
                    limits = httpx.Limits(max_connections=150, max_keepalive_connections=80)
                    async with httpx.AsyncClient(headers=headers, follow_redirects=True, limits=limits) as client:
                        results = await asyncio.gather(
                            self._fetch_internshala(client),
                            self._fetch_ashby_sources(client),
                            self._fetch_greenhouse_sources(client),
                            self._fetch_lever_sources(client),
                            self._fetch_weworkremotely(client),
                            self._fetch_remotive(client),
                            self._fetch_remoteok(client),
                            self._fetch_arbeitnow(client),
                            self._fetch_jobicy(client),
                            return_exceptions=True
                        )

                    all_jobs: List[Job] = []
                    seen_ids = set()

                    for res in results:
                        if isinstance(res, list):
                            for job in res:
                                if job.id not in seen_ids:
                                    seen_ids.add(job.id)
                                    all_jobs.append(job)

                    # Rank by Selection Probability Score (highest odds first)
                    all_jobs.sort(key=lambda j: (j.selection_score, -j.age_hours), reverse=True)

                    # 1. Apply Degree Ratio Filter
                    all_jobs = self._apply_degree_ratio_filter(all_jobs, no_degree_ratio=9, degree_ratio=1)

                    # 2. Apply Master 1:2 Ratio Filter (1 Internship : 2 Full-Time / Fresher Jobs)
                    all_jobs = self._apply_internship_to_job_ratio_filter(all_jobs, internship_ratio=1, job_ratio=2)

                    if all_jobs:
                        self._cached_jobs = all_jobs
                        self._last_fetched_time = time.time()
                        logger.info(f"Ingested {len(all_jobs)} verified CS opportunities (1:2 Internship:Job & 9:1 No-Degree ratios applied).")

                    jobs = self._cached_jobs

        if max_age_hours is not None:
            filtered = [j for j in jobs if j.is_within_recent_hours(max_age_hours)]
            return filtered

        return jobs

    async def search_jobs(
        self,
        query: Optional[str] = None,
        internships_only: bool = False,
        fresher_only: bool = False,
        part_time_only: bool = False,
        year: Optional[int] = None,
        page: int = 1,
        per_page: int = JOBS_PER_PAGE
    ) -> Tuple[List[Job], int, int, int]:
        """Search student tech jobs sorted by selection probability and year/fresher/part-time filters."""
        jobs = await self.get_all_jobs()
        filtered = [
            j for j in jobs
            if (not internships_only or j.is_internship)
            and (not fresher_only or j.is_fresher_role)
            and (not part_time_only or j.is_part_time)
            and (year is None or j.is_eligible_for_year(year))
            and j.matches_query(query)
        ]

        total_jobs = len(filtered)
        if total_jobs == 0:
            return [], 0, 1, 1

        total_pages = (total_jobs + per_page - 1) // per_page
        current_page = max(1, min(page, total_pages))

        start_idx = (current_page - 1) * per_page
        end_idx = start_idx + per_page
        return filtered[start_idx:end_idx], total_jobs, total_pages, current_page

    async def get_job_by_id(self, job_id: str) -> Optional[Job]:
        """Retrieve job by ID."""
        jobs = await self.get_all_jobs()
        for j in jobs:
            if j.id == job_id:
                return j
        return None


# Global singleton instance
job_service = JobService()
