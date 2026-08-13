# CineMatch: Python & SQL Media Recommender

CineMatch is a multi-user movie and TV recommendation system. It pulls data from the TMDB API through a resilient ELT pipeline, then does all the recommendation logic in pure SQL — CTEs, window functions, and anti-joins instead of a Python-side algorithm. The frontend is a Streamlit dashboard supporting both solo recommendations and a "group watch" mode for multiple users at once.

Data flows through three layers: raw JSON responses from TMDB (audited and cached to avoid redundant API calls), staging tables that hold parsed fields, and a normalized curated schema that the app actually queries.

The recommendation engine weights each user's top 4 genres (4/3/2/1 points), aggregates those weights across users for group watch, and ranks titles with `DENSE_RANK()` — sorted by preference score, then rating, then popularity. Already-watched titles are excluded via a `NOT EXISTS` anti-join.

## Running it

```
pip install -r requirements.txt
python verify_pipeline.py
streamlit run src/app.py
```

TMDB API access is optional — a mock client seeds the database out of the box. For live data, add a `.env` with `TMDB_API_KEY` or `TMDB_ACCESS_TOKEN`.

Built with Python, SQLite, and Streamlit.
