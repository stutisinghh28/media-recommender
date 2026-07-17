-- QUERY: Get Recommendations for One or More Users
--
-- HOW THE RECOMMENDATION SYSTEM WORKS
--
-- 1. CALCULATING USER PREFERENCES (CTE: group_genres)
--    Every user has four favourite genres ranked by preference.
--    Instead of treating all genres equally, higher-ranked genres are given
--    more importance using a weighted scoring system:
--
--      • 1st favourite genre → 4 points
--      • 2nd favourite genre → 3 points
--      • 3rd favourite genre → 2 points
--      • 4th favourite genre → 1 point
--
--    If recommendations are being generated for multiple users, the genre
--    scores are added together. This makes genres liked by several users
--    naturally receive a higher overall score.
--
--    Example:
--    If two users both have Sci-Fi as their top genre,
--    Sci-Fi receives 4 + 4 = 8 points.
--
--
-- 2. SCORING EACH TITLE (CTE: title_preference_scores)
--    Every movie or show is compared with the combined genre preferences.
--    The recommendation score is simply the sum of the weights of all
--    matching genres.
--
--    Higher score = Better match with the users' interests.
--
--
-- 3. REMOVING ALREADY WATCHED TITLES
--    Recommendations should only contain new content.
--    Any title already watched by one or more of the selected users is
--    excluded using a NOT EXISTS condition.
--
--
-- 4. RANKING THE RECOMMENDATIONS
--    After calculating the preference score, the results are ranked using
--    DENSE_RANK() to keep the output consistent and deterministic.
--
--    The ranking follows this order:
--      1. Preference Score (Highest first)
--         → Titles that best match user preferences appear first.
--
--      2. TMDB Rating (Highest first)
--         → If two titles have the same score, the higher-rated one is preferred.
--
--      3. Popularity (Highest first)
--         → If there is still a tie, the more popular title is shown first.
--
--
-- :user_ids is a parameter representing one or more user IDs.
-- During execution, Python dynamically builds the IN clause before passing
-- the query to SQLite.

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
