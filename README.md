# CineMatch: Python & SQL Interactive Media Recommender

CineMatch is a multi-user movie and TV show recommendation system. It implements a resilient ELT (Extract, Load, Transform) data pipeline from the TMDB API and uses pure SQL queries (CTEs, window functions, and anti-joins) to execute collaborative recommendations. 

The system features an interactive Streamlit frontend with a premium dark theme dashboard that supports both single-user and multi-user "group watch" recommendations, with dynamic filtering and transparent explainability.

---

## 🏗️ Architecture and Data Flow

CineMatch follows a structured **Raw → Staged → Curated** data flow to ingest, clean, and query media metadata.

```
                  TMDB API (or Mock Ingestion)
                             │
                             ▼ (Ingestion Pipeline)
                    [ Raw Data Layer ]
            (Files under data/raw/ + raw_api_responses DB)
                             │
                             ▼ (Python Parse & Load)
                   [ Staging Data Layer ]
            (staged_genres, staged_titles, etc.)
                             │
                             ▼ (Transaction-Safe Curated ETL)
                   [ Curated Production DB ]
            (users, genres, titles, watch_history, etc.)
```

### 1. Raw Data Layer
- **Ingestion (`src/ingestion.py`):** Fetches metadata from the TMDB API.
- **Auditing & Persistence:** Every raw response is saved as a JSON file in `data/raw/` and logged in the `raw_api_responses` table for reproducibility.
- **Resilience:** Built using `requests` HTTP Adapter with `urllib3` retry adapters. Handles rate limits (HTTP 429) automatically with exponential backoff.
- **Incremental Ingestion:** Checks the curated database's `last_updated` field before making API calls. If the title is present and updated within `CACHE_STALE_DAYS` (configured in `src/config.py`, defaults to `7`), the API call is skipped.

### 2. Staging Data Layer
- Temporary tables in SQLite (`staged_genres`, `staged_titles`, `staged_title_genres`, etc.) containing the parsed raw fields.
- These tables are cleared/refreshed during each ingestion run.

### 3. Curated Production Layer
- A normalized SQL schema containing the final production tables.
- **Transformation (`src/db.py`):** Updates the curated tables from the staging tables using a transaction-safe script.
- **Cascade Deletes Prevention:** Rather than using `INSERT OR REPLACE` (which triggers SQLite `ON DELETE CASCADE` and destroys child rows), it uses `INSERT OR IGNORE` for static mappings and a portable two-step `INSERT OR IGNORE` + `UPDATE` block for titles.

---

## 🧮 Pure SQL Recommendation Engine

All core analytical logic, genre overlap aggregation, exclusion, and ranking are computed **entirely in SQLite** inside `sql/queries.sql`.

### 1. Weighted Preference Scoring
Each user selects their top 4 genres. We map these choices into weights in SQL:
- Rank 1 (Top Genre) = 4 Points
- Rank 2 = 3 Points
- Rank 3 = 2 Points
- Rank 4 = 1 Point

For multiple selected users (e.g. a group watch), these weights are aggregated across users in a Common Table Expression (`group_genres`). For a title, the overall `preference_score` is the sum of the weights of its genres.

### 2. Deterministic Tie-Breaking (Window Functions)
To ensure a deterministic, explainable, and consistent recommendation list, ranking is calculated using `DENSE_RANK()` with the following order:
1. **Primary Sort:** `preference_score` (Desc) - Best match for user tastes.
2. **Tie-Break 1:** `rating` (Desc) - Average user rating from TMDB.
3. **Tie-Break 2:** `popularity` (Desc) - TMDB Popularity Index.

### 3. Watched Exclusion (Anti-Joins)
Titles already watched by **any** target user are filtered out of the recommendation set using a `NOT EXISTS` anti-join clause against the `watch_history` table.

---

## 🚀 Setup & Execution

### Prerequisites
- Python 3.8+
- SQLite (included with Python)

### 1. Installation
Clone the repository, navigate to the folder, and install dependencies:
```bash
pip install -r requirements.txt
```

### 2. API Configuration (Optional)
CineMatch includes a **Mock TMDB Client** that seeds the database and simulates trending lists and details requests out of the box. 

If you want to use the live TMDB API:
1. Create a `.env` file in the project root:
   ```env
   TMDB_API_KEY=your_v3_api_key
   # OR
   TMDB_ACCESS_TOKEN=your_v4_bearer_token
   CACHE_STALE_DAYS=7
   ```
2. The pipeline will automatically switch to live TMDB API ingestion.

### 3. Run the Verification Tests
Execute the verification script to validate schema creation, ingestion, ETL execution, and SQL recommendation logic:
```bash
python verify_pipeline.py
```

### 4. Launch the Streamlit App
Start the interactive dashboard locally:
```bash
streamlit run src/app.py
```
Recommended active workspace setting: `C:\Users\stuti\.gemini\antigravity\scratch\media_recommender`

---

## 📂 Project Directory Structure

```
media_recommender/
├── data/
│   ├── raw/                 # Audited JSON responses from TMDB
│   └── recommender.db       # SQLite curated database
├── sql/
│   ├── schema.sql           # Normalized DDL schema definitions
│   ├── seed.sql             # Default users, preferences, and histories
│   └── queries.sql          # Main CTE recommendation ranking queries
├── src/
│   ├── __init__.py
│   ├── config.py            # Cache, mode, and key configs
│   ├── db.py                # Connection pool, seed loaders, and ETL orchestrator
│   ├── ingestion.py         # TMDB API & Mock ingestion handlers
│   ├── recommender.py       # SQL query compiler & dynamic filtering
│   └── app.py               # Streamlit visual dashboard
├── requirements.txt
├── verify_pipeline.py       # Automated testing script
└── README.md
```
