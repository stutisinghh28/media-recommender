import sqlite3
import logging
from src.db import get_db_connection
from src.config import PROJECT_ROOT

logger = logging.getLogger(__name__)

def get_all_users() -> list:
    """Retrieve all users from the curated database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, created_at FROM users ORDER BY username ASC;")
        return [dict(row) for row in cursor.fetchall()]

def create_user(username: str) -> int:
    """Create a new user. Returns the user_id."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username) VALUES (?);", (username,))
        conn.commit()
        return cursor.lastrowid

def get_all_genres() -> list:
    """Retrieve all unique genres available in the curated database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT genre_id, name FROM genres ORDER BY name ASC;")
        return [dict(row) for row in cursor.fetchall()]

def get_user_preferences(user_id: int) -> list:
    """Retrieve the top 4 genres for a given user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT g.genre_id, g.name, up.preference_order
            FROM user_preferences up
            JOIN genres g ON up.genre_id = g.genre_id
            WHERE up.user_id = ?
            ORDER BY up.preference_order ASC;
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]

def set_user_preferences(user_id: int, genre_ids: list):
    """
    Set the top 4 genres for a user.
    genre_ids must be a list of exactly 4 genre IDs ordered from rank 1 to 4.
    """
    if len(genre_ids) > 4:
        genre_ids = genre_ids[:4]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_preferences WHERE user_id = ?;", (user_id,))
        for idx, g_id in enumerate(genre_ids):
            cursor.execute("""
                INSERT INTO user_preferences (user_id, genre_id, preference_order)
                VALUES (?, ?, ?);
            """, (user_id, g_id, idx + 1))
        conn.commit()

def get_all_titles(limit: int = 100) -> list:
    """Retrieve all titles in the curated database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT title_id, title, media_type, release_date, rating, popularity 
            FROM titles 
            ORDER BY title ASC 
            LIMIT ?;
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

def search_titles(query: str, limit: int = 20) -> list:
    """Search titles by name."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT title_id, title, media_type, release_date, rating, popularity
            FROM titles
            WHERE title LIKE ?
            ORDER BY popularity DESC
            LIMIT ?;
        """, (f"%{query}%", limit))
        return [dict(row) for row in cursor.fetchall()]

def get_user_watch_history(user_id: int) -> list:
    """Retrieve watch history for a given user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.title_id, t.title, t.media_type, t.release_date, wh.watched_at, wh.user_rating
            FROM watch_history wh
            JOIN titles t ON wh.title_id = t.title_id
            WHERE wh.user_id = ?
            ORDER BY wh.watched_at DESC;
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]

def add_to_watch_history(user_id: int, title_id: str, rating: float = None):
    """Add a title to a user's watch history."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO watch_history (user_id, title_id, user_rating)
            VALUES (?, ?, ?);
        """, (user_id, title_id, rating))
        conn.commit()

def get_all_watch_providers() -> list:
    """Retrieve all watch providers in the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT provider_id, provider_name, logo_path FROM watch_providers ORDER BY provider_name ASC;")
        return [dict(row) for row in cursor.fetchall()]

def get_recommendations(
    user_ids: list,
    media_type: str = None,
    min_rating: float = 0.0,
    start_year: int = None,
    end_year: int = None,
    provider_ids: list = None,
    limit: int = 10
) -> list:
    """
    Orchestrate and execute the pure SQL recommendation query loaded from queries.sql,
    appending dynamic filters to the final SELECT statement.
    """
    if not user_ids:
        return []

    # Read base SQL query from sql/queries.sql
    queries_file = PROJECT_ROOT / "sql" / "queries.sql"
    with open(queries_file, "r", encoding="utf-8") as f:
        base_query = f.read()

    # Clean up trailing semicolons or whitespace from the query first
    cleaned_query = base_query.strip().rstrip(";")

    # SQLite python connector does not support direct binding of lists to dynamic "IN (?)" parameters.
    # Therefore we construct the user placeholders dynamically.
    user_placeholders = ",".join("?" for _ in user_ids)
    query = cleaned_query.replace(":user_ids", user_placeholders)

    # Split query at "ORDER BY" to inject dynamic WHERE filters into final SELECT
    parts = query.rsplit("ORDER BY", 1)
    if len(parts) != 2:
        raise ValueError("Invalid sql/queries.sql format: missing 'ORDER BY'")
    
    query_body, query_order = parts[0], parts[1]

    # Collect dynamic filters and their parameters
    filter_clauses = []
    dynamic_params = []

    if media_type:
        filter_clauses.append("m.media_type = ?")
        dynamic_params.append(media_type)

    if min_rating and min_rating > 0:
        filter_clauses.append("m.rating >= ?")
        dynamic_params.append(float(min_rating))

    if start_year:
        filter_clauses.append("strftime('%Y', m.release_date) >= ?")
        dynamic_params.append(str(start_year))

    if end_year:
        filter_clauses.append("strftime('%Y', m.release_date) <= ?")
        dynamic_params.append(str(end_year))

    if provider_ids:
        prov_placeholders = ",".join("?" for _ in provider_ids)
        filter_clauses.append(f"""EXISTS (
            SELECT 1 FROM title_providers tp 
            WHERE tp.title_id = m.title_id 
              AND tp.provider_id IN ({prov_placeholders})
        )""")
        dynamic_params.extend(provider_ids)

    # Build final SQL string
    filter_sql = ""
    if filter_clauses:
        # Since the matching_titles CTE already did the core selection,
        # we append filters to the outer SELECT statement.
        filter_sql = "WHERE " + " AND ".join(filter_clauses)

    final_sql = f"{query_body} {filter_sql} ORDER BY {query_order} LIMIT ?;"
    
    # Position parameter mapping:
    # 1. user_ids (first occurrence in group_genres CTE)
    # 2. user_ids (second occurrence in matching_titles CTE anti-join)
    # 3. dynamic_params (for filters appended at the bottom)
    # 4. limit parameter
    all_params = list(user_ids) + list(user_ids) + dynamic_params + [limit]

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(final_sql, all_params)
        return [dict(row) for row in cursor.fetchall()]
