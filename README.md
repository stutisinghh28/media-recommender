CineMatch: Python & SQL Media Recommender

CineMatch is a multi-user movie and TV recommendation system. It pulls data from the TMDB API through a resilient ELT pipeline, then does all the actual recommendation logic in pure SQL — CTEs, window functions, and anti-joins — instead of leaning on a Python-side algorithm. The frontend is a Streamlit dashboard with a dark theme, supporting both solo recommendations and "group watch" mode for multiple users at once.

How data flows

Data moves through three layers: Raw → Staged → Curated.

Raw layer — src/ingestion.py fetches metadata from TMDB. Every response gets saved as a JSON file under data/raw/ and logged in a raw_api_responses table, so nothing is lost and every pull is auditable. The ingestion uses requests with a retry adapter to handle rate limits (HTTP 429) with exponential backoff. It also checks last_updated before calling the API at all — if a title was updated within CACHE_STALE_DAYS (default 7, set in src/config.py), it skips the call.

Staging layer — Temporary SQLite tables (staged_genres, staged_titles, etc.) hold the parsed fields and get wiped and refreshed on every run.

Curated layer — The final normalized schema. src/db.py moves data from staging into curated tables through a transaction-safe process. It deliberately avoids INSERT OR REPLACE, since that would trigger ON DELETE CASCADE and wipe out related child rows. Instead it uses INSERT OR IGNORE for static mappings and a two-step INSERT OR IGNORE + UPDATE for titles.

The recommendation engine

All ranking logic lives in sql/queries.sql.

Weighted scoring — Each user picks their top 4 genres, which get weighted 4/3/2/1 by rank. For group watch, these weights are aggregated across users in a CTE (group_genres), and a title's preference_score is the sum of its genre weights.

Tie-breaking — Results are ranked with DENSE_RANK(), sorted by preference score first, then average rating, then TMDB popularity — so the output is deterministic and explainable.

Watched exclusion — Anything a target user has already watched gets filtered out with a NOT EXISTS anti-join against watch_history.

Running it

Requires Python 3.8+ (SQLite comes bundled).

pip install -r requirements.txt

TMDB API access is optional — CineMatch ships with a mock client that seeds the database and simulates real responses. To use the live API instead, add a .env file:

TMDB_API_KEY=your_v3_api_key
# or
TMDB_ACCESS_TOKEN=your_v4_bearer_token
CACHE_STALE_DAYS=7

Verify everything works:

python verify_pipeline.py

Then launch the app:

streamlit run src/app.py
Structure
media_recommender/
├── data/
│   ├── raw/                 # Audited JSON responses from TMDB
│   └── recommender.db       # SQLite curated database
├── sql/
│   ├── schema.sql           # DDL schema definitions
│   ├── seed.sql             # Default users, preferences, histories
│   └── queries.sql          # Recommendation ranking queries
├── src/
│   ├── config.py             # Cache, mode, and key configs
│   ├── db.py                 # Connection pool, seed loaders, ETL orchestrator
│   ├── ingestion.py          # TMDB API & mock ingestion handlers
│   ├── recommender.py        # SQL query compiler & dynamic filtering
│   └── app.py                # Streamlit dashboard
├── requirements.txt
├── verify_pipeline.py
└── README.md

Built with Python, SQLite, and Streamlit.
