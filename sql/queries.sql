


WITH group_genres AS (
    
    SELECT 
        genre_id,
        SUM(5 - preference_order) AS combined_weight,
        COUNT(DISTINCT user_id) AS user_match_count
    FROM user_preferences
    WHERE user_id IN (:user_ids)
    GROUP BY genre_id
),
title_preference_scores AS (
    
    SELECT 
        tg.title_id,
        SUM(gg.combined_weight) AS raw_preference_score,
       
        SUM(gg.user_match_count) AS match_strength
    FROM title_genres tg
    JOIN group_genres gg ON tg.genre_id = gg.genre_id
    GROUP BY tg.title_id
),
matching_titles AS (
    
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
        
        
        DENSE_RANK() OVER (
            ORDER BY 
                COALESCE(tps.raw_preference_score, 0) DESC,
                t.rating DESC,
                t.popularity DESC
        ) AS rank
    FROM titles t
    JOIN title_preference_scores tps ON t.title_id = tps.title_id
    WHERE 
        
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
    
    (
        SELECT GROUP_CONCAT(g.name, ', ')
        FROM title_genres tg
        JOIN genres g ON tg.genre_id = g.genre_id
        WHERE tg.title_id = m.title_id
          AND g.genre_id IN (SELECT genre_id FROM group_genres)
    ) AS matching_genres,
   
    (
        SELECT GROUP_CONCAT(g.name, ', ')
        FROM title_genres tg
        JOIN genres g ON tg.genre_id = g.genre_id
        WHERE tg.title_id = m.title_id
    ) AS all_genres
FROM matching_titles m
ORDER BY m.rank ASC;
