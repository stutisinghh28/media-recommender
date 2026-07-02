-- ====================================================================
-- SQL RECOMMENDATION QUERIES
-- ====================================================================

-- --------------------------------------------------------------------
-- QUERY: Get Multi-User or Single-User Recommendations
--
-- RATIONALE & SCORING MATHEMATICS:
-- 1. USER PREFERENCE WEIGHTING (CTE: group_genres)
--    We assign weights to each user's top 4 preferred genres:
--      - Preference Order 1 (Top Genre) = 4 Points
--      - Preference Order 2 = 3 Points
--      - Preference Order 3 = 2 Points
--      - Preference Order 4 = 1 Point
--    For group recommendations, we sum these weights across all target users.
--    This naturally prioritizes genres that are highly rated by multiple users
--    (e.g., if User A ranks Sci-Fi 1 [4 pts] and User B ranks Sci-Fi 1 [4 pts],
--    Sci-Fi gets a combined weight of 8).
--
-- 2. TITLE PREFERENCE SCORING (CTE: title_preference_scores)
--    For each title, we sum the combined weight of its matching genres.
--    Score = SUM(genre_weight for each matching genre).
--
-- 3. EXCLUSION OF WATCHED CONTENT (Anti-Join / NOT EXISTS)
--    We filter out any titles that have already been watched by ANY of the
--    selected users.
--
-- 4. DETERMINISTIC TIE-BREAKING AND RANKING (DENSE_RANK() Window Function)
--    To ensure a fully deterministic, explainable, and consistent recommendation list,
--    ranking is computed in SQLite using DENSE_RANK() with the following order:
--      - Primary Sort: Preference Score (DESC) - How well it matches user tastes.
--      - Tie-Break 1:  TMDB Rating (DESC)      - Quality / Average User Rating.
--      - Tie-Break 2:  Popularity (DESC)       - Popularity / Virality index from TMDB.
-- --------------------------------------------------------------------

-- :user_ids is a parameterized placeholder representing a comma-separated list of user IDs.
-- In SQLite, parameters are bound dynamically. In python, we will construct the IN clause.

WITH group_genres AS (
    -- Collect and aggregate preferences for all selected users
    SELECT 
        genre_id,
        SUM(5 - preference_order) AS combined_weight,
        COUNT(DISTINCT user_id) AS user_match_count
    FROM user_preferences
    WHERE user_id IN (:user_ids)
    GROUP BY genre_id
),
title_preference_scores AS (
    -- Join titles with title_genres and group_genres to calculate overall interest score
    SELECT 
        tg.title_id,
        SUM(gg.combined_weight) AS raw_preference_score,
        -- Number of users in the group who like at least one genre of this title
        SUM(gg.user_match_count) AS match_strength
    FROM title_genres tg
    JOIN group_genres gg ON tg.genre_id = gg.genre_id
    GROUP BY tg.title_id
),
matching_titles AS (
    -- Filter and compute ranking logic
    SELECT 
        t.title_id,
        t.tmdb_id,
        t.title,
        t.media_type,
        t.overview,
        t.release_date,
        t.rating,
        t.popularity,
        t.poster_path,
        COALESCE(tps.raw_preference_score, 0) AS preference_score,
        COALESCE(tps.match_strength, 0) AS match_strength,
        
        -- DENSE_RANK() window function to calculate absolute recommendation rankings
        DENSE_RANK() OVER (
            ORDER BY 
                COALESCE(tps.raw_preference_score, 0) DESC,
                t.rating DESC,
                t.popularity DESC
        ) AS rank
    FROM titles t
    JOIN title_preference_scores tps ON t.title_id = tps.title_id
    WHERE 
        -- 1. Anti-join to exclude already-watched titles by ANY of the target users
        NOT EXISTS (
            SELECT 1 
            FROM watch_history wh
            WHERE wh.title_id = t.title_id
            AND wh.user_id IN (:user_ids)
        )
)
SELECT 
    m.rank,
    m.title_id,
    m.tmdb_id,
    m.title,
    m.media_type,
    m.overview,
    m.release_date,
    m.rating,
    m.popularity,
    m.poster_path,
    m.preference_score,
    m.match_strength,
    -- Get list of matching genres for display/explainability
    (
        SELECT GROUP_CONCAT(g.name, ', ')
        FROM title_genres tg
        JOIN genres g ON tg.genre_id = g.genre_id
        WHERE tg.title_id = m.title_id
          AND g.genre_id IN (SELECT genre_id FROM group_genres)
    ) AS matching_genres,
    -- Get list of all genres for this title
    (
        SELECT GROUP_CONCAT(g.name, ', ')
        FROM title_genres tg
        JOIN genres g ON tg.genre_id = g.genre_id
        WHERE tg.title_id = m.title_id
    ) AS all_genres
FROM matching_titles m
ORDER BY m.rank ASC;
