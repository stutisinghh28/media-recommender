-- ====================================================================
-- RAW DATA LAYER
-- ====================================================================
CREATE TABLE IF NOT EXISTS raw_api_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    endpoint TEXT NOT NULL,
    query_params TEXT,
    response_body TEXT NOT NULL,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================================
-- STAGING DATA LAYER (Temporary tables cleared/refreshed during ETL)
-- ====================================================================
DROP TABLE IF EXISTS staged_genres;
CREATE TABLE staged_genres (
    genre_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    media_type TEXT NOT NULL, -- 'movie' or 'tv'
    PRIMARY KEY (genre_id, media_type)
);

DROP TABLE IF EXISTS staged_titles;
CREATE TABLE staged_titles (
    tmdb_id INTEGER NOT NULL,
    media_type TEXT NOT NULL, -- 'movie' or 'tv'
    title TEXT NOT NULL,
    overview TEXT,
    release_date TEXT,
    rating REAL,
    vote_count INTEGER,
    popularity REAL,
    poster_path TEXT,
    PRIMARY KEY (tmdb_id, media_type)
);

DROP TABLE IF EXISTS staged_title_genres;
CREATE TABLE staged_title_genres (
    tmdb_id INTEGER NOT NULL,
    media_type TEXT NOT NULL,
    genre_id INTEGER NOT NULL,
    PRIMARY KEY (tmdb_id, media_type, genre_id)
);

DROP TABLE IF EXISTS staged_title_cast;
CREATE TABLE staged_title_cast (
    tmdb_id INTEGER NOT NULL,
    media_type TEXT NOT NULL,
    actor_name TEXT NOT NULL,
    character_name TEXT,
    cast_order INTEGER,
    PRIMARY KEY (tmdb_id, media_type, actor_name, cast_order)
);

DROP TABLE IF EXISTS staged_title_providers;
CREATE TABLE staged_title_providers (
    tmdb_id INTEGER NOT NULL,
    media_type TEXT NOT NULL,
    provider_id INTEGER NOT NULL,
    provider_name TEXT NOT NULL,
    logo_path TEXT,
    display_priority INTEGER,
    PRIMARY KEY (tmdb_id, media_type, provider_id)
);

-- ====================================================================
-- CURATED (PRODUCTION) DATA LAYER
-- ====================================================================

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Genres Table (normalized)
CREATE TABLE IF NOT EXISTS genres (
    genre_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

-- Titles Table (normalized, unique ID resolves overlaps between movies and shows)
CREATE TABLE IF NOT EXISTS titles (
    title_id TEXT PRIMARY KEY, -- format: '{media_type}_{tmdb_id}' e.g., 'movie_550', 'tv_1399'
    tmdb_id INTEGER NOT NULL,
    media_type TEXT CHECK(media_type IN ('movie', 'tv')) NOT NULL,
    title TEXT NOT NULL,
    overview TEXT,
    release_date DATE,
    rating REAL DEFAULT 0.0,
    vote_count INTEGER DEFAULT 0,
    popularity REAL DEFAULT 0.0,
    poster_path TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on tmdb_id and media_type for faster updates/lookups
CREATE UNIQUE INDEX IF NOT EXISTS idx_titles_tmdb_media ON titles(tmdb_id, media_type);

-- Title-Genre Mapping
CREATE TABLE IF NOT EXISTS title_genres (
    title_id TEXT NOT NULL,
    genre_id INTEGER NOT NULL,
    PRIMARY KEY (title_id, genre_id),
    FOREIGN KEY (title_id) REFERENCES titles(title_id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genres(genre_id) ON DELETE CASCADE
);

-- Title-Cast Mapping
CREATE TABLE IF NOT EXISTS title_cast (
    title_id TEXT NOT NULL,
    actor_name TEXT NOT NULL,
    character_name TEXT,
    cast_order INTEGER,
    PRIMARY KEY (title_id, actor_name, cast_order),
    FOREIGN KEY (title_id) REFERENCES titles(title_id) ON DELETE CASCADE
);

-- Watch Providers Table
CREATE TABLE IF NOT EXISTS watch_providers (
    provider_id INTEGER PRIMARY KEY,
    provider_name TEXT NOT NULL,
    logo_path TEXT
);

-- Title-Provider Mapping
CREATE TABLE IF NOT EXISTS title_providers (
    title_id TEXT NOT NULL,
    provider_id INTEGER NOT NULL,
    display_priority INTEGER,
    PRIMARY KEY (title_id, provider_id),
    FOREIGN KEY (title_id) REFERENCES titles(title_id) ON DELETE CASCADE,
    FOREIGN KEY (provider_id) REFERENCES watch_providers(provider_id) ON DELETE CASCADE
);

-- User Preferences (Exactly top 4 preferred genres per user)
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,
    preference_order INTEGER CHECK(preference_order BETWEEN 1 AND 4),
    PRIMARY KEY (user_id, preference_order),
    UNIQUE (user_id, genre_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genres(genre_id) ON DELETE CASCADE
);

-- Watch History
CREATE TABLE IF NOT EXISTS watch_history (
    user_id INTEGER NOT NULL,
    title_id TEXT NOT NULL,
    watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_rating REAL CHECK(user_rating BETWEEN 0.0 AND 10.0),
    PRIMARY KEY (user_id, title_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (title_id) REFERENCES titles(title_id) ON DELETE CASCADE
);
