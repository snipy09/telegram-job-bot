"""
Curated Registry of 100+ Top Tech Sources, Public ATS Endpoints & Tech Feeds.
Includes Top 500 Tech Giants, Tier-1 AI Unicorns, DevTool Leaders, Internshala, and Tech Aggregators.
"""

# 1. Internshala Direct Paid Internship Feeds (CS, Web, AI/ML, Python, Java, Data)
INTERNSHALA_URLS = [
    "https://internshala.com/internships/work-from-home-computer-science-internships/",
    "https://internshala.com/internships/computer-science-internship/",
    "https://internshala.com/internships/web-development-internship/",
    "https://internshala.com/internships/python-django-internship/",
    "https://internshala.com/internships/java-internship/",
    "https://internshala.com/internships/artificial-intelligence-ai-internship/",
    "https://internshala.com/internships/data-science-internship/",
    "https://internshala.com/internships/information-technology-internship/"
]

# 2. Ashby HQ Public API Targets (Tier-1 AI Unicorns & High-Growth DevTools - 35 Sources)
ASHBY_SOURCES = [
    {"name": "Linear", "slug": "linear", "category": "Dev Tools"},
    {"name": "Perplexity AI", "slug": "perplexity", "category": "AI / Search"},
    {"name": "Cursor / Anysphere", "slug": "cursor", "category": "AI / IDE"},
    {"name": "Replit", "slug": "replit", "category": "Cloud / IDE"},
    {"name": "Ramp", "slug": "ramp", "category": "Fintech"},
    {"name": "PostHog", "slug": "posthog", "category": "Product Analytics"},
    {"name": "Together AI", "slug": "togetherai", "category": "AI / Cloud"},
    {"name": "Elicit", "slug": "elicit", "category": "AI / Research"},
    {"name": "Vercel", "slug": "vercel", "category": "Frontend Cloud"},
    {"name": "Mistral AI", "slug": "mistralai", "category": "AI / LLM"},
    {"name": "Brex", "slug": "brex", "category": "Fintech"},
    {"name": "Deel", "slug": "deel", "category": "Global HR / Fintech"},
    {"name": "Rippling", "slug": "rippling", "category": "Enterprise SaaS"},
    {"name": "Retool", "slug": "retool", "category": "Internal Tools"},
    {"name": "ElevenLabs", "slug": "elevenlabs", "category": "AI / Voice"},
    {"name": "Groq", "slug": "groq", "category": "AI Hardware / Cloud"},
    {"name": "Weights & Biases", "slug": "weightsandbiases", "category": "MLOps"},
    {"name": "Modal", "slug": "modal", "category": "Serverless AI"},
    {"name": "LangChain", "slug": "langchain", "category": "AI Frameworks"},
    {"name": "Pinecone", "slug": "pinecone", "category": "Vector DB"},
    {"name": "Runway", "slug": "runwayml", "category": "AI Video"},
    {"name": "Stability AI", "slug": "stabilityai", "category": "GenAI"},
    {"name": "Jasper AI", "slug": "jasper", "category": "GenAI"},
    {"name": "Character AI", "slug": "characterai", "category": "Conversational AI"},
    {"name": "Sierra AI", "slug": "sierra", "category": "Enterprise AI"},
    {"name": "Synthesia", "slug": "synthesia", "category": "AI Video"},
    {"name": "Harvey AI", "slug": "harvey", "category": "Legal AI"},
    {"name": "Glean", "slug": "glean", "category": "Enterprise Search"},
    {"name": "Writer", "slug": "writer", "category": "Enterprise GenAI"},
    {"name": "Lovable", "slug": "lovable", "category": "Fullstack AI"},
    {"name": "Supabase", "slug": "supabase", "category": "Open Source Backend"},
    {"name": "Resend", "slug": "resend", "category": "Developer Email"},
    {"name": "Raycast", "slug": "raycast", "category": "Productivity"},
    {"name": "Prisma", "slug": "prisma", "category": "ORM / Data"},
    {"name": "Vapi AI", "slug": "vapi", "category": "Voice AI"}
]

# 3. Greenhouse Public API Targets (Top 500 Tech Giants, Cloud Titans & Unicorns - 45 Sources)
GREENHOUSE_SOURCES = [
    {"name": "Stripe", "slug": "stripe", "category": "Fintech / Payments"},
    {"name": "OpenAI", "slug": "openai", "category": "AI / AGI"},
    {"name": "Anthropic", "slug": "anthropic", "category": "AI / Safety"},
    {"name": "Postman", "slug": "postman", "category": "API Platform"},
    {"name": "Scale AI", "slug": "scaleai", "category": "AI Data"},
    {"name": "Cloudflare", "slug": "cloudflare", "category": "Cloud / Edge"},
    {"name": "Databricks", "slug": "databricks", "category": "Data & AI"},
    {"name": "GitLab", "slug": "gitlab", "category": "DevOps"},
    {"name": "Figma", "slug": "figma", "category": "Design Tech"},
    {"name": "Snowflake", "slug": "snowflake", "category": "Cloud Data"},
    {"name": "MongoDB", "slug": "mongodb", "category": "Database"},
    {"name": "DoorDash", "slug": "doordash", "category": "Logistics Tech"},
    {"name": "Coinbase", "slug": "coinbase", "category": "Crypto / Web3"},
    {"name": "Robinhood", "slug": "robinhood", "category": "Fintech"},
    {"name": "Datadog", "slug": "datadog", "category": "Observability"},
    {"name": "Elastic", "slug": "elastic", "category": "Search / Big Data"},
    {"name": "HashiCorp", "slug": "hashicorp", "category": "Cloud Infrastructure"},
    {"name": "Atlassian", "slug": "atlassian", "category": "Developer Collaboration"},
    {"name": "Uber", "slug": "uber", "category": "Mobility Tech"},
    {"name": "Airbnb", "slug": "airbnb", "category": "Travel Tech"},
    {"name": "Pinterest", "slug": "pinterest", "category": "Social & Search"},
    {"name": "Twilio", "slug": "twilio", "category": "Cloud Communications"},
    {"name": "GitHub", "slug": "github", "category": "Developer Platform"},
    {"name": "Notion", "slug": "notion", "category": "Workspace Tech"},
    {"name": "Airtable", "slug": "airtable", "category": "No-Code Database"},
    {"name": "Discord", "slug": "discord", "category": "Communications"},
    {"name": "Zoom", "slug": "zoom", "category": "Video Infra"},
    {"name": "Docker", "slug": "docker", "category": "Containers"},
    {"name": "Redis", "slug": "redis", "category": "In-Memory Data"},
    {"name": "Sentry", "slug": "sentry", "category": "Error Monitoring"},
    {"name": "Grafana Labs", "slug": "grafanalabs", "category": "Open Source Metrics"},
    {"name": "Pulumi", "slug": "pulumi", "category": "Infrastructure as Code"},
    {"name": "Temporal", "slug": "temporalio", "category": "Microservice Workflows"},
    {"name": "PlanetScale", "slug": "planetscale", "category": "Serverless MySQL"},
    {"name": "Render", "slug": "render", "category": "Cloud Hosting"},
    {"name": "Fly.io", "slug": "flyio", "category": "Global Application Cloud"},
    {"name": "Neon", "slug": "neon", "category": "Serverless Postgres"},
    {"name": "Doppler", "slug": "doppler", "category": "Secret Management"},
    {"name": "Warp", "slug": "warp", "category": "AI Terminal"},
    {"name": "ClickHouse", "slug": "clickhouse", "category": "Fast Analytics DB"},
    {"name": "Astronomer", "slug": "astronomer", "category": "Airflow Data Platform"},
    {"name": "Kong", "slug": "kong", "category": "API Gateway"},
    {"name": "CockroachDB", "slug": "cockroachdb", "category": "Distributed SQL"},
    {"name": "Zapier", "slug": "zapier", "category": "Workflow Automation"},
    {"name": "Automattic", "slug": "automattic", "category": "Open Source Web"}
]

# 4. Lever Public API Targets (Global Tech Leaders - 15 Sources)
LEVER_SOURCES = [
    {"name": "Spotify", "slug": "spotify", "category": "Audio Streaming"},
    {"name": "Canva", "slug": "canva", "category": "Visual Design"},
    {"name": "Framer", "slug": "framer", "category": "Interactive Design"},
    {"name": "ClearTax", "slug": "cleartax", "category": "Fintech"},
    {"name": "Instawork", "slug": "instawork", "category": "Labor Marketplace"},
    {"name": "Netflix", "slug": "netflix", "category": "Streaming / Media"},
    {"name": "Lyft", "slug": "lyft", "category": "Rideshare Tech"},
    {"name": "Palantir", "slug": "palantir", "category": "Enterprise Big Data"},
    {"name": "Kraken", "slug": "kraken", "category": "Crypto Exchange"},
    {"name": "Yelp", "slug": "yelp", "category": "Local Discovery"},
    {"name": "Webflow", "slug": "webflow", "category": "Visual Development"},
    {"name": "Buffer", "slug": "buffer", "category": "Social Media Tech"},
    {"name": "Sourcegraph", "slug": "sourcegraph", "category": "Code Intelligence"},
    {"name": "Coursera", "slug": "coursera", "category": "EdTech"},
    {"name": "Udemy", "slug": "udemy", "category": "EdTech"}
]

# 5. We Work Remotely Feeds (High-Quality Global Tech Remote - 4 Feeds)
WWR_FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    "https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss"
]

# 6. High-Yield Tech Aggregators (8 Endpoints)
AGGREGATOR_APIS = {
    "remotive": [
        "https://remotive.com/api/remote-jobs?category=software-dev&limit=50",
        "https://remotive.com/api/remote-jobs?category=data&limit=30",
        "https://remotive.com/api/remote-jobs?category=qa&limit=20"
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
