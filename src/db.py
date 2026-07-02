import sqlite3
import logging
from pathlib import Path
from src.config import DB_PATH, PROJECT_ROOT

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def get_db_connection() -> sqlite3.Connection:
    """Establish a connection to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys support in SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(force_reseed: bool = False):
    """
    Initialize the database using the schema.sql DDL script.
    If force_reseed is True or if the users table is empty, run seed.sql.
    """
    schema_path = PROJECT_ROOT / "sql" / "schema.sql"
    seed_path = PROJECT_ROOT / "sql" / "seed.sql"

    logger.info(f"Initializing database at: {DB_PATH}")
    
    with get_db_connection() as conn:
        # 1. Execute schema.sql
        with open(schema_path, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        logger.info("Database schema loaded successfully.")

        # Check if users are present to decide if we should seed
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]

        # 2. Execute seed.sql if requested or if DB is empty
        if force_reseed or user_count == 0:
            logger.info("Seeding initial mock data...")
            with open(seed_path, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
            logger.info("Database seeded successfully.")

def clear_staging_tables(conn: sqlite3.Connection):
    """Truncate staging tables to prepare for a new ETL batch."""
    staging_tables = [
        "staged_genres",
        "staged_titles",
        "staged_title_genres",
        "staged_title_cast",
        "staged_title_providers"
    ]
    cursor = conn.cursor()
    for table in staging_tables:
        cursor.execute(f"DELETE FROM {table};")
    conn.commit()
    logger.info("Cleared all staging tables.")

def run_curated_etl(conn: sqlite3.Connection):
    """
    Execute SQL transformation queries to move data from the staged layer
    to the curated (production) layer. Runs in a transaction.
    """
    cursor = conn.cursor()
    try:
        # Start transaction explicitly
        cursor.execute("BEGIN TRANSACTION;")

        logger.info("Running ETL: Staged -> Curated...")

        # 1. Upsert genres (use IGNORE to prevent cascade delete from REPLACE)
        cursor.execute("""
            INSERT OR IGNORE INTO genres (genre_id, name)
            SELECT DISTINCT genre_id, name
            FROM staged_genres;
        """)

        # 2. Upsert titles (using INSERT OR IGNORE + UPDATE to prevent cascade delete and syntax errors)
        cursor.execute("""
            INSERT OR IGNORE INTO titles (
                title_id, tmdb_id, media_type, title, overview, 
                release_date, rating, vote_count, popularity, poster_path, last_updated
            )
            SELECT 
                printf('%s_%d', media_type, tmdb_id) AS title_id,
                tmdb_id,
                media_type,
                title,
                overview,
                release_date,
                rating,
                vote_count,
                popularity,
                poster_path,
                CURRENT_TIMESTAMP AS last_updated
            FROM staged_titles;
        """)
        
        cursor.execute("""
            UPDATE titles 
            SET 
                rating = (SELECT rating FROM staged_titles s WHERE s.tmdb_id = titles.tmdb_id AND s.media_type = titles.media_type),
                vote_count = (SELECT vote_count FROM staged_titles s WHERE s.tmdb_id = titles.tmdb_id AND s.media_type = titles.media_type),
                popularity = (SELECT popularity FROM staged_titles s WHERE s.tmdb_id = titles.tmdb_id AND s.media_type = titles.media_type),
                last_updated = CURRENT_TIMESTAMP
            WHERE EXISTS (
                SELECT 1 FROM staged_titles s 
                WHERE s.tmdb_id = titles.tmdb_id AND s.media_type = titles.media_type
            );
        """)

        # 3. Upsert title genres mapping (using IGNORE to prevent cascade delete)
        cursor.execute("""
            INSERT OR IGNORE INTO title_genres (title_id, genre_id)
            SELECT 
                printf('%s_%d', media_type, tmdb_id) AS title_id,
                genre_id
            FROM staged_title_genres;
        """)

        # 4. Upsert title cast mapping
        cursor.execute("""
            INSERT OR IGNORE INTO title_cast (title_id, actor_name, character_name, cast_order)
            SELECT 
                printf('%s_%d', media_type, tmdb_id) AS title_id,
                actor_name,
                character_name,
                cast_order
            FROM staged_title_cast;
        """)

        # 5. Upsert watch providers
        cursor.execute("""
            INSERT OR IGNORE INTO watch_providers (provider_id, provider_name, logo_path)
            SELECT DISTINCT 
                provider_id,
                provider_name,
                logo_path
            FROM staged_title_providers;
        """)

        # 6. Upsert title watch provider mappings
        cursor.execute("""
            INSERT OR IGNORE INTO title_providers (title_id, provider_id, display_priority)
            SELECT 
                printf('%s_%d', media_type, tmdb_id) AS title_id,
                provider_id,
                display_priority
            FROM staged_title_providers;
        """)

        conn.commit()
        logger.info("ETL completed successfully. Production database updated.")
    except Exception as e:
        conn.rollback()
        logger.error(f"ETL pipeline failed. Rolled back changes. Error: {e}")
        raise e
