"""
Structured Dataset of High-Priority Job Boards, ATS Endpoints & Tech Feeds.
Monitors Top 500 tech companies, global unicorns, venture-backed AI startups, and Internshala.
"""

# Internshala Tech & CS Internship Feeds
INTERNSHALA_URLS = [
    "https://internshala.com/internships/work-from-home-computer-science-internships/",
    "https://internshala.com/internships/computer-science-internship/",
    "https://internshala.com/internships/web-development-internship/",
    "https://internshala.com/internships/python-django-internship/"
]

# Ashby HQ Public API Targets (Tier-1 AI & High-Growth Unicorns)
ASHBY_SOURCES = [
    {"name": "Linear", "slug": "linear", "stage": "Series B"},
    {"name": "Perplexity AI", "slug": "perplexity", "stage": "Series B"},
    {"name": "Cursor", "slug": "cursor", "stage": "Series A"},
    {"name": "Replit", "slug": "replit", "stage": "Series B"},
    {"name": "Ramp", "slug": "ramp", "stage": "Series D"},
    {"name": "PostHog", "slug": "posthog", "stage": "Series B"},
    {"name": "Together AI", "slug": "togetherai", "stage": "Series A"},
    {"name": "Elicit", "slug": "elicit", "stage": "Seed"},
    {"name": "Vercel", "slug": "vercel", "stage": "Series E"},
    {"name": "Mistral AI", "slug": "mistralai", "stage": "Series A"},
    {"name": "Brex", "slug": "brex", "stage": "Series D"},
    {"name": "Deel", "slug": "deel", "stage": "Series D"},
    {"name": "Rippling", "slug": "rippling", "stage": "Series F"},
    {"name": "Retool", "slug": "retool", "stage": "Series C"},
    {"name": "ElevenLabs", "slug": "elevenlabs", "stage": "Series B"},
    {"name": "Groq", "slug": "groq", "stage": "Series C"},
    {"name": "Weights & Biases", "slug": "weightsandbiases", "stage": "Series C"},
    {"name": "Modal", "slug": "modal", "stage": "Series A"}
]

# Greenhouse Public API Targets (Top 500 Tech Companies, Public Tech & Global Unicorns)
GREENHOUSE_SOURCES = [
    {"name": "Stripe", "slug": "stripe", "stage": "Growth"},
    {"name": "Postman", "slug": "postman", "stage": "Series D"},
    {"name": "Vercel", "slug": "vercel", "stage": "Series E"},
    {"name": "Scale AI", "slug": "scaleai", "stage": "Series F"},
    {"name": "Cloudflare", "slug": "cloudflare", "stage": "Public"},
    {"name": "Supabase", "slug": "supabase", "stage": "Series B"},
    {"name": "Databricks", "slug": "databricks", "stage": "Pre-IPO"},
    {"name": "GitLab", "slug": "gitlab", "stage": "Public"},
    {"name": "Figma", "slug": "figma", "stage": "Pre-IPO"},
    {"name": "Snowflake", "slug": "snowflake", "stage": "Public"},
    {"name": "MongoDB", "slug": "mongodb", "stage": "Public"},
    {"name": "DoorDash", "slug": "doordash", "stage": "Public"},
    {"name": "Coinbase", "slug": "coinbase", "stage": "Public"},
    {"name": "Robinhood", "slug": "robinhood", "stage": "Public"},
    {"name": "Datadog", "slug": "datadog", "stage": "Public"},
    {"name": "Elastic", "slug": "elastic", "stage": "Public"},
    {"name": "HashiCorp", "slug": "hashicorp", "stage": "Public"},
    {"name": "Atlassian", "slug": "atlassian", "stage": "Public"},
    {"name": "Uber", "slug": "uber", "stage": "Public"},
    {"name": "Airbnb", "slug": "airbnb", "stage": "Public"},
    {"name": "Pinterest", "slug": "pinterest", "stage": "Public"},
    {"name": "Twilio", "slug": "twilio", "stage": "Public"}
]

# Lever Public API Targets (Global Tech Leaders)
LEVER_SOURCES = [
    {"name": "Spotify", "slug": "spotify", "stage": "Public"},
    {"name": "Canva", "slug": "canva", "stage": "Growth"},
    {"name": "Framer", "slug": "framer", "stage": "Series C"},
    {"name": "ClearTax", "slug": "cleartax", "stage": "Series C"},
    {"name": "Instawork", "slug": "instawork", "stage": "Series D"},
    {"name": "Netflix", "slug": "netflix", "stage": "Public"},
    {"name": "Lyft", "slug": "lyft", "stage": "Public"},
    {"name": "Palantir", "slug": "palantir", "stage": "Public"},
    {"name": "Kraken", "slug": "kraken", "stage": "Pre-IPO"}
]

# We Work Remotely Tech Category Feeds
WWR_FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss"
]

# Aggregator Tech Endpoints
AGGREGATOR_APIS = {
    "remotive": [
        "https://remotive.com/api/remote-jobs?category=software-dev&limit=50",
        "https://remotive.com/api/remote-jobs?category=data&limit=30"
    ],
    "jobicy": [
        "https://jobicy.com/api/v2/remote-jobs?count=30&tag=developer",
        "https://jobicy.com/api/v2/remote-jobs?count=20&tag=python",
        "https://jobicy.com/api/v2/remote-jobs?count=20&tag=react",
        "https://jobicy.com/api/v2/remote-jobs?count=20&tag=engineering"
    ],
    "arbeitnow": "https://www.arbeitnow.com/api/job-board-api",
    "remoteok": "https://remoteok.com/api"
}
