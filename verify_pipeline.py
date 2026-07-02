import sys
import logging
from src.db import init_db, get_db_connection, run_curated_etl, clear_staging_tables
from src.ingestion import run_ingestion_pipeline
import src.recommender as rec

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("verify_pipeline")

def test_pipeline():
    logger.info("====================================================")
    logger.info("STARTING PIPELINE & QUERY LAYER VERIFICATION")
    logger.info("====================================================")
    
    # 1. Initialize Database & Seed
    logger.info("Step 1: Initializing and seeding the SQLite database...")
    init_db(force_reseed=True)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM titles;")
        title_count_start = cursor.fetchone()[0]
        logger.info(f"Database initialized with {title_count_start} seed titles.")
        assert title_count_start > 0, "Failed to seed default titles."

    # 2. Run Ingestion Pipeline (Mock mode by default, unless API keys exist)
    logger.info("\nStep 2: Simulating ingestion pipeline run...")
    # Clear staging first
    with get_db_connection() as conn:
        clear_staging_tables(conn)
        
    ingested_count = run_ingestion_pipeline(limit_per_type=5)
    logger.info(f"Ingested {ingested_count} new raw response items into staging.")
    
    # 3. Execute Curated ETL Transform
    logger.info("\nStep 3: Orchestrating Curated ETL Transform...")
    with get_db_connection() as conn:
        run_curated_etl(conn)
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM titles;")
        title_count_end = cursor.fetchone()[0]
        logger.info(f"Total titles after ETL sync: {title_count_end}")
        assert title_count_end >= title_count_start, "Curated titles table should not shrink."

    # 4. Verify Single-User recommendations
    logger.info("\nStep 4: Verifying Single-User recommendations...")
    # Alice (user_id = 1) has:
    # Preferred Genres: Science Fiction (878), Action (28), Adventure (12), Thriller (53)
    # Watched: Inception (movie_27205), The Matrix (movie_603), The Avengers (movie_24428)
    # Note: Inception is Action/Adventure/Sci-Fi. The Matrix is Action/Sci-Fi. The Avengers is Action/Adventure/Sci-Fi.
    # Unwatched titles that match Alice's preferences:
    # - Interstellar (movie_157336) -> Adventure/Drama/Sci-Fi -> matches Sci-Fi & Adventure. Combined weight: 4 + 2 = 6 points. Rating: 8.4, Pop: 145.2.
    # - Avengers: Endgame (movie_299534) -> Action/Adventure/Sci-Fi -> matches Sci-Fi, Action, Adventure. Weight: 4 + 3 + 2 = 9 points. Rating: 8.3, Pop: 115.6.
    # - Dune (movie_438631) -> Sci-Fi/Adventure -> matches Sci-Fi & Adventure. Weight: 4 + 2 = 6 points. Rating: 7.8, Pop: 135.4. (if Dune is ingested from mock).
    # Since Avengers: Endgame has 9 points, it should rank HIGHER than Interstellar (6 points) despite Interstellar having a slightly higher rating,
    # because Preference Score is the primary sorting key!
    # Let's verify this!
    
    alice_recs = rec.get_recommendations(user_ids=[1], limit=5)
    logger.info("Alice's Recommendations:")
    for r in alice_recs:
        logger.info(f"Rank {r['rank']}: {r['title']} | Pref Score: {r['preference_score']} | Rating: {r['rating']} | Pop: {r['popularity']} | Match: {r['matching_genres']}")
        
    # Assertions for Alice:
    # - Watched titles (Inception, The Matrix, The Avengers) MUST NOT be present
    watched_titles = ["Inception", "The Matrix", "The Avengers"]
    for r in alice_recs:
        assert r["title"] not in watched_titles, f"Watched title '{r['title']}' was incorrectly suggested!"
        
    # - Assert deterministic ordering (primary: preference_score, tiebreak1: rating, tiebreak2: popularity)
    for i in range(len(alice_recs) - 1):
        r1 = alice_recs[i]
        r2 = alice_recs[i + 1]
        
        # Check order condition:
        # r1.pref_score > r2.pref_score OR
        # (r1.pref_score == r2.pref_score AND r1.rating > r2.rating) OR
        # (r1.pref_score == r2.pref_score AND r1.rating == r2.rating AND r1.popularity >= r2.popularity)
        ordered = (r1["preference_score"] > r2["preference_score"]) or \
                  (r1["preference_score"] == r2["preference_score"] and r1["rating"] > r2["rating"]) or \
                  (r1["preference_score"] == r2["preference_score"] and r1["rating"] == r2["rating"] and r1["popularity"] >= r2["popularity"])
        
        assert ordered, f"Ranking order violation between '{r1['title']}' and '{r2['title']}':\n{r1}\n{r2}"
        
    logger.info("Alice's recommendation assertions PASSED.")

    # 5. Verify Group (Multi-User) recommendations
    logger.info("\nStep 5: Verifying Collaborative Group Watch recommendations...")
    # Alice (user_id = 1) + Bob (user_id = 2)
    # Alice prefers: Sci-Fi (4), Action (3), Adventure (2), Thriller (1)
    # Bob prefers: Sci-Fi (4), Drama (3), Mystery (2), Sci-Fi & Fantasy (1)
    # Overlapping preferred genres: Sci-Fi (combined weight = 8)
    # Excluded watched titles for group:
    #   Alice watched: Inception, The Matrix, The Avengers
    #   Bob watched: Inception, Interstellar
    # Combined excluded: Inception, The Matrix, The Avengers, Interstellar.
    # Let's run group watch suggestions for Alice + Bob:
    group_recs = rec.get_recommendations(user_ids=[1, 2], limit=5)
    logger.info("Alice + Bob Group Recommendations:")
    for r in group_recs:
        logger.info(f"Rank {r['rank']}: {r['title']} | Pref Score: {r['preference_score']} | Rating: {r['rating']} | Match: {r['matching_genres']}")
        
    # Assertions for Group:
    # - Exclude watched titles of BOTH Alice & Bob (includes Interstellar!)
    group_watched_titles = ["Inception", "The Matrix", "The Avengers", "Interstellar"]
    for r in group_recs:
        assert r["title"] not in group_watched_titles, f"Group watched title '{r['title']}' was incorrectly suggested!"
        
    logger.info("Group recommendation assertions PASSED.")
    
    logger.info("\n====================================================")
    logger.info("ALL PIPELINE & QUERY LAYER TESTS COMPLETED SUCCESSFULLY!")
    logger.info("====================================================")

if __name__ == "__main__":
    try:
        test_pipeline()
        sys.exit(0)
    except AssertionError as ae:
        logger.error(f"Verification assertion failed: {ae}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Verification encountered unexpected error: {e}")
        sys.exit(1)
