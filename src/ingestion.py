import json
import time
import urllib.parse
import logging
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from src.config import (
    TMDB_API_KEY,
    TMDB_ACCESS_TOKEN,
    CACHE_STALE_DAYS,
    RAW_DATA_DIR,
    is_mock_mode
)
from src.db import get_db_connection

logger = logging.getLogger(__name__)

# Base URL for TMDB API v3
TMDB_BASE_URL = "https://api.themoviedb.org/3"

class TMDBClient:
    """
    Resilient TMDB API client supporting Bearer tokens, API keys,
    automatic retries, backoff, and rate limit handling.
    """
    def __init__(self):
        self.session = requests.Session()
        
        # Configure Retries with Exponential Backoff
        # Will retry on 429 (Too Many Requests), 500, 502, 503, 504
        retries = Retry(
            total=5,
            backoff_factor=1.0,  # [1.0s, 2.0s, 4.0s, 8.0s, 16.0s]
            status_forcelist=[429, 500, 502, 503, 504],
            raise_on_status=False
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        
        # Prepare headers
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        if TMDB_ACCESS_TOKEN:
            self.headers["Authorization"] = f"Bearer {TMDB_ACCESS_TOKEN}"
            self.api_key = None
        else:
            self.api_key = TMDB_API_KEY

    def _get(self, endpoint: str, params: dict = None) -> dict:
        """Helper to send a GET request, handle rate limits and return JSON."""
        url = f"{TMDB_BASE_URL}/{endpoint.lstrip('/')}"
        
        # Merge API Key if not using Bearer Token
        req_params = params.copy() if params else {}
        if self.api_key:
            req_params["api_key"] = self.api_key

        # Rate Limiting Guard: Wait slightly to be safe (TMDB removed strict 40req/10s limit, but it's polite)
        time.sleep(0.2)

        try:
            response = self.session.get(url, headers=self.headers, params=req_params, timeout=10)
            
            # If rate limited (429) and urllib3 retry failed to hold back, do a manual wait
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 5))
                logger.warning(f"Rate limited (429). Sleeping for {retry_after} seconds...")
                time.sleep(retry_after)
                response = self.session.get(url, headers=self.headers, params=req_params, timeout=10)
                
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {url} with params {params}: {e}")
            raise e

    def fetch_genres(self, media_type: str) -> dict:
        """Fetch list of genres for 'movie' or 'tv'."""
        return self._get(f"genre/{media_type}/list")

    def fetch_trending(self, media_type: str, page: int = 1) -> dict:
        """Fetch trending media of type 'movie' or 'tv' for the week."""
        # Standardize endpoint to trending/{media_type}/week
        return self._get(f"trending/{media_type}/week", {"page": page})

    def fetch_details(self, media_type: str, tmdb_id: int) -> dict:
        """Fetch detailed information for a movie or TV show, including credits and watch providers."""
        params = {
            "append_to_response": "credits,watch/providers"
        }
        return self._get(f"{media_type}/{tmdb_id}", params)


# ====================================================================
# MOCK API GENERATOR (Fallback when API keys are absent)
# ====================================================================

MOCK_TITLES = [
    # Movies
    {
        "tmdb_id": 507086,
        "media_type": "movie",
        "title": "Jurassic World Dominion",
        "overview": "Four years after Isla Nublar was destroyed, dinosaurs now live—and hunt—alongside humans all over the world.",
        "release_date": "2022-06-01",
        "rating": 6.9,
        "vote_count": 5200,
        "popularity": 75.8,
        "poster_path": "/kAVR2Z8vHkvbrh3JZAx6G0H8g93.jpg",
        "genres": [{"id": 28, "name": "Action"}, {"id": 12, "name": "Adventure"}, {"id": 878, "name": "Science Fiction"}],
        "cast": [
            {"name": "Chris Pratt", "character": "Owen Grady", "order": 0},
            {"name": "Bryce Dallas Howard", "character": "Claire Dearing", "order": 1},
            {"name": "Laura Dern", "character": "Dr. Ellie Sattler", "order": 2}
        ],
        "providers": [
            {"provider_id": 8, "provider_name": "Netflix", "logo_path": "/p1E68616i62V80QNzpqoMRBECHO.jpg", "display_priority": 1}
        ]
    },
    {
        "tmdb_id": 438631,
        "media_type": "movie",
        "title": "Dune",
        "overview": "Paul Atreides, a brilliant and gifted young man born into a great destiny beyond his understanding, must travel to the most dangerous planet in the universe to ensure the future of his family and his people.",
        "release_date": "2021-09-15",
        "rating": 7.8,
        "vote_count": 9400,
        "popularity": 135.4,
        "poster_path": "/d5NXSklXkiLZIe17St8r27Z3Y91.jpg",
        "genres": [{"id": 878, "name": "Science Fiction"}, {"id": 12, "name": "Adventure"}],
        "cast": [
            {"name": "Timothée Chalamet", "character": "Paul Atreides", "order": 0},
            {"name": "Rebecca Ferguson", "character": "Lady Jessica Atreides", "order": 1},
            {"name": "Oscar Isaac", "character": "Duke Leto Atreides", "order": 2}
        ],
        "providers": [
            {"provider_id": 119, "provider_name": "Amazon Prime Video", "logo_path": "/h5G0w251Ey5J5y94Lg76sF52j4V.jpg", "display_priority": 1},
            {"provider_id": 8, "provider_name": "Netflix", "logo_path": "/p1E68616i62V80QNzpqoMRBECHO.jpg", "display_priority": 2}
        ]
    },
    {
        "tmdb_id": 315162,
        "media_type": "movie",
        "title": "Puss in Boots: The Last Wish",
        "overview": "Puss in Boots discovers that his passion for adventure has taken its toll: he has burned through eight of his nine lives, leaving him with only one life left.",
        "release_date": "2022-12-07",
        "rating": 8.3,
        "vote_count": 6800,
        "popularity": 92.7,
        "poster_path": "/kuf6HgcVUGlUW3Zrxj8OUtXQI7x.jpg",
        "genres": [{"id": 16, "name": "Animation"}, {"id": 12, "name": "Adventure"}, {"id": 35, "name": "Comedy"}, {"id": 10751, "name": "Family"}, {"id": 14, "name": "Fantasy"}],
        "cast": [
            {"name": "Antonio Banderas", "character": "Puss in Boots (voice)", "order": 0},
            {"name": "Salma Hayek", "character": "Kitty Softpaws (voice)", "order": 1},
            {"name": "Harvey Guillén", "character": "Perrito (voice)", "order": 2}
        ],
        "providers": [
            {"provider_id": 337, "provider_name": "Disney Plus", "logo_path": "/9A1q8MK6Z3w74v4TB4ihR6AX5xL.jpg", "display_priority": 1}
        ]
    },
    {
        "tmdb_id": 240,
        "media_type": "movie",
        "title": "The Godfather Part II",
        "overview": "In the continuing saga of the Corleone crime family, a young Vito Corleone grows up in Sicily and in 1910s New York.",
        "release_date": "1974-12-20",
        "rating": 8.6,
        "vote_count": 11500,
        "popularity": 78.3,
        "poster_path": "/bMadFzhjy9Ui6vfg2111u0ZPd7r.jpg",
        "genres": [{"id": 18, "name": "Drama"}, {"id": 80, "name": "Crime"}],
        "cast": [
            {"name": "Al Pacino", "character": "Michael Corleone", "order": 0},
            {"name": "Robert De Niro", "character": "Vito Corleone (young)", "order": 1},
            {"name": "Robert Duvall", "character": "Tom Hagen", "order": 2}
        ],
        "providers": [
            {"provider_id": 15, "provider_name": "Hulu", "logo_path": "/8bq7JgH46G6JpHtA5fM8U17U5jK.jpg", "display_priority": 1}
        ]
    },
    {
        "tmdb_id": 550,
        "media_type": "movie",
        "title": "Fight Club",
        "overview": "A ticking-time-bomb insomniac and a slippery soap salesman channel male aggression into a shocking new form of therapy.",
        "release_date": "1999-10-15",
        "rating": 8.4,
        "vote_count": 27000,
        "popularity": 95.1,
        "poster_path": "/adw6L11119xrVhyue56a0rtwR7t.jpg",
        "genres": [{"id": 18, "name": "Drama"}, {"id": 53, "name": "Thriller"}],
        "cast": [
            {"name": "Edward Norton", "character": "The Narrator", "order": 0},
            {"name": "Brad Pitt", "character": "Tyler Durden", "order": 1},
            {"name": "Helena Bonham Carter", "character": "Marla Singer", "order": 2}
        ],
        "providers": [
            {"provider_id": 8, "provider_name": "Netflix", "logo_path": "/p1E68616i62V80QNzpqoMRBECHO.jpg", "display_priority": 1}
        ]
    },
    # TV Shows
    {
        "tmdb_id": 100088,
        "media_type": "tv",
        "title": "The Last of Us",
        "overview": "Twenty years after modern civilization has been destroyed, Joel, a hardened survivor, is hired to smuggle Ellie, a 14-year-old girl, out of an oppressive quarantine zone.",
        "release_date": "2023-01-15",
        "rating": 8.6,
        "vote_count": 4200,
        "popularity": 180.2,
        "poster_path": "/uKvH5G0w251Ey5J5y94Lg76sF52.jpg",
        "genres": [{"id": 18, "name": "Drama"}, {"id": 10765, "name": "Sci-Fi & Fantasy"}, {"id": 10759, "name": "Action & Adventure"}],
        "cast": [
            {"name": "Pedro Pascal", "character": "Joel Miller", "order": 0},
            {"name": "Bella Ramsey", "character": "Ellie Williams", "order": 1}
        ],
        "providers": [
            {"provider_id": 8, "provider_name": "Netflix", "logo_path": "/p1E68616i62V80QNzpqoMRBECHO.jpg", "display_priority": 1},
            {"provider_id": 337, "provider_name": "Disney Plus", "logo_path": "/9A1q8MK6Z3w74v4TB4ihR6AX5xL.jpg", "display_priority": 2}
        ]
    },
    {
        "tmdb_id": 60625,
        "media_type": "tv",
        "title": "Rick and Morty",
        "overview": "An relations-driven animated series about the infinite adventures of Rick, a genius-alcoholic scientist, and his grandson Morty, a normal 14-year-old boy.",
        "release_date": "2013-12-02",
        "rating": 8.7,
        "vote_count": 8700,
        "popularity": 160.5,
        "poster_path": "/84iaiuG3w74v4TB4ihR6AX5xL.jpg",
        "genres": [{"id": 16, "name": "Animation"}, {"id": 35, "name": "Comedy"}, {"id": 10765, "name": "Sci-Fi & Fantasy"}],
        "cast": [
            {"name": "Justin Roiland", "character": "Rick / Morty (voice)", "order": 0},
            {"name": "Chris Parnell", "character": "Jerry Smith (voice)", "order": 1}
        ],
        "providers": [
            {"provider_id": 15, "provider_name": "Hulu", "logo_path": "/8bq7JgH46G6JpHtA5fM8U17U5jK.jpg", "display_priority": 1},
            {"provider_id": 8, "provider_name": "Netflix", "logo_path": "/p1E68616i62V80QNzpqoMRBECHO.jpg", "display_priority": 2}
        ]
    },
    {
        "tmdb_id": 76331,
        "media_type": "tv",
        "title": "Succession",
        "overview": "The Roy family is known for controlling the biggest media and entertainment company in the world. However, their world changes when their father steps down.",
        "release_date": "2018-06-03",
        "rating": 8.3,
        "vote_count": 2800,
        "popularity": 92.4,
        "poster_path": "/succession_poster.jpg",
        "genres": [{"id": 18, "name": "Drama"}],
        "cast": [
            {"name": "Brian Cox", "character": "Logan Roy", "order": 0},
            {"name": "Jeremy Strong", "character": "Kendall Roy", "order": 1},
            {"name": "Sarah Snook", "character": "Siobhan 'Shiv' Roy", "order": 2}
        ],
        "providers": [
            {"provider_id": 350, "provider_name": "Apple TV Plus", "logo_path": "/6nusrfQLpVKuDG47nJ7uV75Q0tV.jpg", "display_priority": 1}
        ]
    }
]

class MockTMDBClient:
    """Mock TMDB client to return pre-coded responses for demo/test purposes."""
    def fetch_genres(self, media_type: str) -> dict:
        if media_type == "movie":
            return {"genres": [
                {"id": 28, "name": "Action"}, {"id": 12, "name": "Adventure"},
                {"id": 16, "name": "Animation"}, {"id": 35, "name": "Comedy"},
                {"id": 80, "name": "Crime"}, {"id": 99, "name": "Documentary"},
                {"id": 18, "name": "Drama"}, {"id": 10751, "name": "Family"},
                {"id": 14, "name": "Fantasy"}, {"id": 36, "name": "History"},
                {"id": 27, "name": "Horror"}, {"id": 10402, "name": "Music"},
                {"id": 9648, "name": "Mystery"}, {"id": 10749, "name": "Romance"},
                {"id": 878, "name": "Science Fiction"}, {"id": 10770, "name": "TV Movie"},
                {"id": 53, "name": "Thriller"}, {"id": 10752, "name": "War"},
                {"id": 37, "name": "Western"}
            ]}
        else:
            return {"genres": [
                {"id": 10759, "name": "Action & Adventure"}, {"id": 16, "name": "Animation"},
                {"id": 35, "name": "Comedy"}, {"id": 80, "name": "Crime"},
                {"id": 99, "name": "Documentary"}, {"id": 18, "name": "Drama"},
                {"id": 10751, "name": "Family"}, {"id": 9648, "name": "Mystery"},
                {"id": 10762, "name": "Kids"}, {"id": 10763, "name": "News"},
                {"id": 10764, "name": "Reality"}, {"id": 10765, "name": "Sci-Fi & Fantasy"},
                {"id": 10766, "name": "Soap"}, {"id": 10767, "name": "Talk"},
                {"id": 10768, "name": "War & Politics"}, {"id": 37, "name": "Western"}
            ]}

    def fetch_trending(self, media_type: str, page: int = 1) -> dict:
        results = [t for t in MOCK_TITLES if t["media_type"] == media_type]
        return {"results": [{"id": r["tmdb_id"], "media_type": r["media_type"]} for r in results]}

    def fetch_details(self, media_type: str, tmdb_id: int) -> dict:
        for t in MOCK_TITLES:
            if t["media_type"] == media_type and t["tmdb_id"] == tmdb_id:
                # Wrap it in details API format
                details = {
                    "id": t["tmdb_id"],
                    "title" if media_type == "movie" else "name": t["title"],
                    "overview": t["overview"],
                    "release_date" if media_type == "movie" else "first_air_date": t["release_date"],
                    "vote_average": t["rating"],
                    "vote_count": t["vote_count"],
                    "popularity": t["popularity"],
                    "poster_path": t["poster_path"],
                    "genres": t["genres"],
                    "credits": {"cast": t["cast"]},
                    "watch/providers": {
                        "results": {
                            "US": {
                                "flatrate": t["providers"]
                            }
                        }
                    }
                }
                return details
        raise ValueError(f"Mock Details not found for {media_type} with ID {tmdb_id}")


# ====================================================================
# PIPELINE ORCHESTRATION & INGESTION
# ====================================================================

def persist_raw_response(endpoint: str, query_params: dict, response_data: dict, conn) -> Path:
    """
    Saves raw response JSON to a file in data/raw/ and also logs it in
    the raw_api_responses SQL table for audibility.
    """
    # 1. Save to SQLite table
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO raw_api_responses (endpoint, query_params, response_body)
        VALUES (?, ?, ?);
    """, (endpoint, json.dumps(query_params), json.dumps(response_data)))
    conn.commit()

    # 2. Save to file system
    clean_endpoint = endpoint.replace("/", "_").strip("_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{clean_endpoint}_{timestamp}.json"
    file_path = RAW_DATA_DIR / filename
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(response_data, f, indent=2)
        
    return file_path

def is_title_cache_valid(media_type: str, tmdb_id: int, conn) -> bool:
    """
    Incremental fetch check.
    Checks if a title already exists in the curated table and if its
    last_updated timestamp is fresher than CACHE_STALE_DAYS.
    """
    title_id = f"{media_type}_{tmdb_id}"
    cursor = conn.cursor()
    cursor.execute("""
        SELECT last_updated FROM titles WHERE title_id = ?;
    """, (title_id,))
    row = cursor.fetchone()
    
    if not row:
        return False  # Not in DB, must fetch
        
    last_updated_str = row[0]
    try:
        # SQLite CURRENT_TIMESTAMP is in YYYY-MM-DD HH:MM:SS format
        last_updated = datetime.strptime(last_updated_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        # Fallback if stored in another format
        last_updated = datetime.now() - timedelta(days=CACHE_STALE_DAYS + 1)
        
    age = datetime.utcnow() - last_updated
    is_valid = age.days < CACHE_STALE_DAYS
    
    if is_valid:
        logger.info(f"Cache valid for {title_id} (fetched {age.days} days ago). Skipping API call.")
    else:
        logger.info(f"Cache stale or missing for {title_id} (fetched {age.days} days ago). Fetching fresh data.")
        
    return is_valid

def load_genres_to_staging(genres_payload: dict, media_type: str, conn):
    """Load raw genres list into staged_genres table."""
    cursor = conn.cursor()
    genres = genres_payload.get("genres", [])
    
    for genre in genres:
        cursor.execute("""
            INSERT OR REPLACE INTO staged_genres (genre_id, name, media_type)
            VALUES (?, ?, ?);
        """, (genre["id"], genre["name"], media_type))
    conn.commit()

def load_title_to_staging(details_payload: dict, media_type: str, conn):
    """
    Parses a single movie/TV details payload and maps it into
    the corresponding staging tables: staged_titles, staged_title_genres,
    staged_title_cast, staged_title_providers.
    """
    cursor = conn.cursor()
    
    tmdb_id = details_payload.get("id")
    title = details_payload.get("title") if media_type == "movie" else details_payload.get("name")
    overview = details_payload.get("overview")
    release_date = details_payload.get("release_date") if media_type == "movie" else details_payload.get("first_air_date")
    rating = details_payload.get("vote_average", 0.0)
    vote_count = details_payload.get("vote_count", 0)
    popularity = details_payload.get("popularity", 0.0)
    poster_path = details_payload.get("poster_path")

    if not tmdb_id or not title:
        logger.warning("Invalid details payload. Skipping staging.")
        return

    # 1. Insert into staged_titles
    cursor.execute("""
        INSERT OR REPLACE INTO staged_titles (
            tmdb_id, media_type, title, overview, release_date, rating, vote_count, popularity, poster_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (tmdb_id, media_type, title, overview, release_date, rating, vote_count, popularity, poster_path))

    # 2. Insert into staged_title_genres
    genres = details_payload.get("genres", [])
    for genre in genres:
        cursor.execute("""
            INSERT OR REPLACE INTO staged_title_genres (tmdb_id, media_type, genre_id)
            VALUES (?, ?, ?);
        """, (tmdb_id, media_type, genre["id"]))

    # 3. Insert into staged_title_cast (Top 5 cast members)
    cast_list = details_payload.get("credits", {}).get("cast", [])
    for cast_member in cast_list[:5]:
        actor_name = cast_member.get("name")
        character_name = cast_member.get("character")
        cast_order = cast_member.get("order", 99)
        if actor_name:
            cursor.execute("""
                INSERT OR REPLACE INTO staged_title_cast (tmdb_id, media_type, actor_name, character_name, cast_order)
                VALUES (?, ?, ?, ?, ?);
            """, (tmdb_id, media_type, actor_name, character_name, cast_order))

    # 4. Insert into staged_title_providers (Streaming availability)
    # Extracts US flatrate providers by default
    providers_results = details_payload.get("watch/providers", {}).get("results", {})
    us_providers = providers_results.get("US", {})
    flatrate_providers = us_providers.get("flatrate", [])
    
    for provider in flatrate_providers:
        p_id = provider.get("provider_id")
        p_name = provider.get("provider_name")
        logo = provider.get("logo_path")
        priority = provider.get("display_priority", 99)
        
        if p_id and p_name:
            cursor.execute("""
                INSERT OR REPLACE INTO staged_title_providers (
                    tmdb_id, media_type, provider_id, provider_name, logo_path, display_priority
                ) VALUES (?, ?, ?, ?, ?, ?);
            """, (tmdb_id, media_type, p_id, p_name, logo, priority))

    conn.commit()

def run_ingestion_pipeline(media_types=None, limit_per_type=10) -> int:
    """
    Orchestrate the ingestion run:
    1. Determine mode (API vs Mock)
    2. Fetch and stage genres
    3. Fetch trending lists and filter by incremental fetch validity
    4. For each fresh title, fetch details, persist raw response, and staging map
    5. Return count of newly ingested titles
    """
    if media_types is None:
        media_types = ["movie", "tv"]
        
    client = MockTMDBClient() if is_mock_mode() else TMDBClient()
    logger.info(f"Running Ingestion Pipeline in {'MOCK' if is_mock_mode() else 'LIVE API'} mode...")

    newly_ingested = 0
    
    with get_db_connection() as conn:
        for media_type in media_types:
            # Step A: Fetch and stage genres
            try:
                logger.info(f"Fetching genres for {media_type}...")
                genres_data = client.fetch_genres(media_type)
                persist_raw_response(f"genre/{media_type}/list", {}, genres_data, conn)
                load_genres_to_staging(genres_data, media_type, conn)
            except Exception as e:
                logger.error(f"Failed to fetch genres for {media_type}: {e}")
                continue

            # Step B: Fetch trending titles to ingest
            try:
                logger.info(f"Fetching trending {media_type} shows...")
                trending_data = client.fetch_trending(media_type, page=1)
                persist_raw_response(f"trending/{media_type}/week", {"page": 1}, trending_data, conn)
                
                results = trending_data.get("results", [])
                ingest_count = 0
                for item in results:
                    if ingest_count >= limit_per_type:
                        break
                    
                    tmdb_id = item.get("id")
                    if not tmdb_id:
                        continue
                    
                    # Step C: Incremental fetch check before hitting TMDB details
                    if is_title_cache_valid(media_type, tmdb_id, conn):
                        continue
                    
                    # Step D: Fetch detailed title payload
                    logger.info(f"Fetching details for {media_type} ID: {tmdb_id}...")
                    details_data = client.fetch_details(media_type, tmdb_id)
                    
                    # Step E: Persist raw detail JSON
                    persist_raw_response(f"{media_type}/{tmdb_id}", {}, details_data, conn)
                    
                    # Step F: Staging ingestion
                    load_title_to_staging(details_data, media_type, conn)
                    
                    newly_ingested += 1
                    ingest_count += 1
            except Exception as e:
                logger.error(f"Failed to process trending list for {media_type}: {e}")
                continue
                
    return newly_ingested
