import time
import pandas as pd
import streamlit as st
from datetime import datetime
from src.config import is_mock_mode, CACHE_STALE_DAYS
from src.db import init_db, get_db_connection, run_curated_etl, clear_staging_tables
from src.ingestion import run_ingestion_pipeline
import src.recommender as rec


# Set page configuration with premium dark theme vibes
st.set_page_config(
    page_title="CineMatch | SQL-Powered Media Recommender",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply custom premium styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .main {
        background: radial-gradient(circle at top right, #1a1525, #0d0b11);
        color: #f1ecf9;
    }
    
    /* Header Styles */
    .title-text {
        font-weight: 800;
        background: linear-gradient(90deg, #ff4b4b, #8b5cf6, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        margin-bottom: 0.2rem;
    }
    .subtitle-text {
        font-weight: 300;
        color: #a78bfa;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Custom Glassmorphic Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        margin-bottom: 1rem;
        transition: transform 0.2s ease-in-out, border-color 0.2s ease;
    }
    .glass-card:hover {
        transform: translateY(-2px);
        border-color: rgba(139, 92, 246, 0.4);
    }
    
    /* Recommendation Item Grid */
    .rec-item {
        background: rgba(20, 16, 28, 0.6);
        border-left: 5px solid #8b5cf6;
        padding: 1rem;
        border-radius: 0 12px 12px 0;
        margin-bottom: 1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 30px;
        margin-right: 0.35rem;
        margin-bottom: 0.35rem;
        text-transform: uppercase;
    }
    .badge-genre {
        background: rgba(139, 92, 246, 0.15);
        color: #c084fc;
        border: 1px solid rgba(139, 92, 246, 0.3);
    }
    .badge-matching {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .badge-score {
        background: linear-gradient(135deg, #ec4899, #8b5cf6);
        color: white;
        font-size: 0.85rem;
        font-weight: 800;
    }
    .badge-rating {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    
    /* Sidebar styling customization */
    .css-163oo07 {
        background-color: #0f0d15 !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Database on first startup
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state['db_initialized'] = True

# App Title & Header
st.markdown('<div class="title-text">CineMatch</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-text">Interactive Python & SQL-driven Multi-User Media Recommendation System</div>', unsafe_allow_html=True)

# Sidebar - Navigation & Data Ingestion Pipeline Controls
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=400&auto=format&fit=crop&q=60", use_container_width=True)
    st.markdown("### 🎛️ Navigation")
    app_mode = st.radio("Go to:", ["🎉 Recommendations", "👤 Profile & Preferences", "⚙️ Data pipeline (ELT)"])
    
    st.markdown("---")
    st.markdown("### 📡 TMDB Ingestion Pipeline")
    st.info(f"**Pipeline Mode:** `{'MOCK' if is_mock_mode() else 'LIVE API'}`\n\nIncremental threshold is `{CACHE_STALE_DAYS} days`.")
    
    if st.button("🔄 Sync Live Data"):
        with st.status("Running Data Sync...", expanded=True) as status:
            try:
                status.update(label="Syncing Genres & Trending Data from TMDB...", state="running")
                # Clear staging tables before sync
                with get_db_connection() as conn:
                    clear_staging_tables(conn)
                
                # Fetch new raw payloads and write to staged tables
                new_titles = run_ingestion_pipeline(limit_per_type=10)
                status.update(label=f"Ingested {new_titles} raw payloads into staging. Running ELT transforms...", state="running")
                
                # Run the transaction-safe SQL Curated ETL
                with get_db_connection() as conn:
                    run_curated_etl(conn)
                
                status.update(label=f"Pipeline run complete! Ingested and curated {new_titles} titles.", state="complete")
                st.success("Database synced successfully!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                status.update(label="Sync failed!", state="error")
                st.error(f"Error executing ingestion: {e}")

# Load all core metadata
users = rec.get_all_users()
genres = rec.get_all_genres()
providers = rec.get_all_watch_providers()

# Handle empty database safety
if not users:
    st.warning("No users found. Please initialize the database or add a user.")
    if st.button("Seed Database"):
        init_db(force_reseed=True)
        st.rerun()
    st.stop()


# ====================================================================
# PAGE 1: RECOMMENDATIONS (SINGLE-USER & GROUP MODE)
# ====================================================================
if app_mode == "🎉 Recommendations":
    st.markdown("## 🍿 Suggest Must-Watch Titles")
    st.write("Excludes already-watched titles. Scores based on combined genre priorities, rating, and popularity.")
    
    # User selection row
    col1, col2 = st.columns([2, 1])
    with col1:
        # Determine mode
        rec_type = st.segmented_control("Recommendation Mode:", ["Single User", "Group Watch"], default="Single User")
    
    with col2:
        if rec_type == "Single User":
            # Single user selection dropdown
            usernames = [u["username"] for u in users]
            selected_username = st.selectbox("Select User:", usernames)
            selected_user_id = next(u["user_id"] for u in users if u["username"] == selected_username)
            selected_user_ids = [selected_user_id]
        else:
            # Multi-user selection checkboxes
            selected_usernames = st.multiselect("Select Group Members:", [u["username"] for u in users], default=[u["username"] for u in users[:2]])
            selected_user_ids = [u["user_id"] for u in users if u["username"] in selected_usernames]

    # Filters row
    st.markdown("#### 🔍 Filter Suggestions")
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1:
        media_filter = st.selectbox("Media Type", ["All", "Movie Only", "TV Show Only"])
        media_param = None
        if media_filter == "Movie Only":
            media_param = "movie"
        elif media_filter == "TV Show Only":
            media_param = "tv"
            
    with f_col2:
        min_rating = st.slider("Minimum Rating", 0.0, 10.0, 5.0, 0.5)
        
    with f_col3:
        current_year = datetime.now().year
        year_range = st.slider("Release Year", 1950, current_year, (1990, current_year))
        
    with f_col4:
        provider_names = [p["provider_name"] for p in providers]
        selected_provider_names = st.multiselect("Streaming On:", provider_names)
        provider_ids_param = [p["provider_id"] for p in providers if p["provider_name"] in selected_provider_names] if selected_provider_names else None

    # Trigger recommendation query
    if not selected_user_ids:
        st.warning("Please select at least one user to get recommendations.")
    else:
        # Query DB using pure SQL
        recommendations = rec.get_recommendations(
            user_ids=selected_user_ids,
            media_type=media_param,
            min_rating=min_rating,
            start_year=year_range[0],
            end_year=year_range[1],
            provider_ids=provider_ids_param,
            limit=12
        )
        
        # Display Group Preference analysis (Explainability)
        with st.expander("📊 Recommendation Logic & Overlapping Genres", expanded=True):
            # Gather all preferences for selected users
            pref_data = []
            for uid in selected_user_ids:
                u_name = next(u["username"] for u in users if u["user_id"] == uid)
                u_prefs = rec.get_user_preferences(uid)
                for p in u_prefs:
                    pref_data.append({
                        "User": u_name,
                        "Genre": p["name"],
                        "Rank": p["preference_order"],
                        "Weight": 5 - p["preference_order"]
                    })
            
            if pref_data:
                df_pref = pd.DataFrame(pref_data)
                
                # Show overlapping genres
                genre_weights = df_pref.groupby("Genre")["Weight"].sum().reset_index()
                genre_weights = genre_weights.sort_values(by="Weight", ascending=False)
                
                col_ex1, col_ex2 = st.columns([1, 1])
                with col_ex1:
                    st.markdown("**Top Genre Interests (Summed Weight across Selected Group):**")
                    genres_list_str = " | ".join([f"**{row['Genre']}** ({row['Weight']} pts)" for _, row in genre_weights.iterrows()])
                    st.markdown(genres_list_str)
                with col_ex2:
                    st.markdown("**Deterministic SQL Ranking Formula:**")
                    st.caption("Rank = DENSE_RANK() OVER (ORDER BY Preference_Score DESC, Rating DESC, Popularity DESC)")
            else:
                st.caption("No preferences defined for the selected users.")

        st.markdown("### 🎬 Top Suggestions")
        if not recommendations:
            st.info("No matching recommendations found. Try loosening the filter constraints!")
        else:
            # Layout items in a grid
            for idx, r in enumerate(recommendations):
                # 3 column items per row
                if idx % 3 == 0:
                    cols = st.columns(3)
                
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div class="glass-card">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                            <span class="badge badge-score">Rank #{r['rank']}</span>
                            <span class="badge badge-rating">⭐ {r['rating']:.1f}</span>
                        </div>
                        <h3 style="margin-top: 0.2rem; margin-bottom:0.2rem;">{r['title']}</h3>
                        <div style="margin-bottom:0.5rem;">
                            <span style="font-size: 0.85rem; color:#888;">{r['media_type'].upper()} &bull; {r['release_date']} &bull; Pop: {r['popularity']:.1f}</span>
                        </div>
                        <p style="font-size:0.85rem; height: 75px; overflow:hidden; text-overflow:ellipsis; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical;">
                            {r['overview'] if r['overview'] else 'No description available.'}
                        </p>
                        <div style="margin-top:0.5rem; margin-bottom:0.5rem;">
                            <strong style="font-size:0.8rem; color:#a78bfa;">Genre Overlap Match:</strong><br/>
                            {', '.join([f'<span class="badge badge-matching">{g.strip()}</span>' for g in r['matching_genres'].split(',')]) if r['matching_genres'] else '<span style="font-size:0.8rem; color:#666;">Generic fallback</span>'}
                        </div>
                        <div style="font-size:0.75rem; color:#aaa; margin-top:0.3rem;">
                            <strong>All Genres:</strong> {r['all_genres']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)


# ====================================================================
# PAGE 2: PROFILE & PREFERENCES (EDITING / CREATING)
# ====================================================================
elif app_mode == "👤 Profile & Preferences":
    st.markdown("## 👤 Manage Users & Preferences")
    
    tab_pref, tab_history, tab_create = st.tabs(["🎯 Genre Preferences", "📜 Watch History", "➕ Create User"])
    
    # TAB: Genre Preferences
    with tab_pref:
        usernames = [u["username"] for u in users]
        sel_user_name = st.selectbox("Select User to Edit Preferences:", usernames)
        sel_user = next(u for u in users if u["username"] == sel_user_name)
        
        # Get existing top genres
        current_prefs = rec.get_user_preferences(sel_user["user_id"])
        st.write("Top 4 Genres (1 is highest priority, 4 is lowest):")
        
        # Load all genres names
        all_genre_names = [g["name"] for g in genres]
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            g1 = st.selectbox("Rank 1 (Top Choice)", all_genre_names, index=all_genre_names.index(current_prefs[0]["name"]) if len(current_prefs) > 0 else 0)
            g2 = st.selectbox("Rank 2", all_genre_names, index=all_genre_names.index(current_prefs[1]["name"]) if len(current_prefs) > 1 else 1)
        with col_g2:
            g3 = st.selectbox("Rank 3", all_genre_names, index=all_genre_names.index(current_prefs[2]["name"]) if len(current_prefs) > 2 else 2)
            g4 = st.selectbox("Rank 4", all_genre_names, index=all_genre_names.index(current_prefs[3]["name"]) if len(current_prefs) > 3 else 3)
            
        if st.button("Save Preferences"):
            selected_genre_ids = [
                next(g["genre_id"] for g in genres if g["name"] == name)
                for name in [g1, g2, g3, g4]
            ]
            
            # Validation: duplicate check
            if len(set(selected_genre_ids)) < 4:
                st.error("Duplicate genres detected! Please assign 4 unique genres.")
            else:
                rec.set_user_preferences(sel_user["user_id"], selected_genre_ids)
                st.success(f"Preferences saved for {sel_user_name}!")
                st.rerun()

    # TAB: Watch History Logging
    with tab_history:
        sel_user_name_h = st.selectbox("Select User for Watch History:", usernames, key="history_select")
        sel_user_h = next(u for u in users if u["username"] == sel_user_name_h)
        
        col_h1, col_h2 = st.columns([2, 1])
        with col_h1:
            st.markdown("#### ✍️ Log a Title as Watched")
            search_query = st.text_input("Search Titles in DB to Log:", placeholder="Type title name...")
            
            if search_query:
                search_results = rec.search_titles(search_query)
                if not search_results:
                    st.info("No matching titles found. (Hint: Ingest new titles via the sidebar).")
                else:
                    st.write("Search Results:")
                    for title_item in search_results:
                        sub_col1, sub_col2 = st.columns([3, 1])
                        with sub_col1:
                            st.write(f"**{title_item['title']}** ({title_item['media_type'].upper()}, {title_item['release_date']})")
                        with sub_col2:
                            if st.button("Log Watched", key=f"log_{title_item['title_id']}"):
                                rec.add_to_watch_history(sel_user_h["user_id"], title_item["title_id"])
                                st.toast(f"Logged '{title_item['title']}' as watched!")
                                st.rerun()
                                
        with col_h2:
            st.markdown("#### 📜 Already Watched Titles")
            user_history = rec.get_user_watch_history(sel_user_h["user_id"])
            if not user_history:
                st.caption("No titles logged in watch history yet.")
            else:
                for h in user_history:
                    st.markdown(f"&bull; **{h['title']}** ({h['media_type'].upper()} &bull; {h['release_date']})")

    # TAB: Create User
    with tab_create:
        st.markdown("#### ➕ Add New User Profile")
        new_username = st.text_input("Enter New Username:")
        if st.button("Create Profile"):
            if not new_username.strip():
                st.error("Username cannot be blank.")
            elif any(u["username"].lower() == new_username.strip().lower() for u in users):
                st.error("Username already exists.")
            else:
                new_uid = rec.create_user(new_username.strip())
                # Default preferences to random standard genres to avoid crash
                default_gids = [g["genre_id"] for g in genres[:4]]
                rec.set_user_preferences(new_uid, default_gids)
                st.success(f"Profile created for '{new_username}' with default preferences! Configure their top genres in the first tab.")
                st.rerun()


# ====================================================================
# PAGE 3: ETL & DATA FLOW DIAGNOSTICS
# ====================================================================
elif app_mode == "⚙️ Data pipeline (ELT)":
    st.markdown("## ⚙️ Data Flow & Database Diagnostics")
    
    st.markdown("""
    This screen displays details about the Raw → Staged → Curated database architecture.
    You can inspect raw API ingestion tables, clear staging tables, or force a complete DB reseed.
    """)
    
    # Database stats
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM raw_api_responses;")
        raw_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM titles;")
        curated_titles_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM title_genres;")
        genre_links_count = cursor.fetchone()[0]

    stat_col1, stat_col2, stat_col3 = st.columns(3)
    with stat_col1:
        st.metric("Raw API Response Payloads", raw_count)
    with stat_col2:
        st.metric("Curated Production Titles", curated_titles_count)
    with stat_col3:
        st.metric("Title-Genre Link Records", genre_links_count)

    # Database DDL Visualization / Staging Inspection
    st.markdown("### 📊 Database Diagnostics Logs")
    with get_db_connection() as conn:
        # Show recent raw responses
        st.markdown("**Recent Raw Ingested API Responses (raw_api_responses):**")
        df_raw = pd.read_sql_query("SELECT id, endpoint, query_params, fetched_at FROM raw_api_responses ORDER BY fetched_at DESC LIMIT 5;", conn)
        st.dataframe(df_raw, use_container_width=True)

        # Show staged data counts
        st.markdown("**Staging Table Record Counts (Ready for Curated ETL):**")
        staged_counts = {}
        for tbl in ["staged_genres", "staged_titles", "staged_title_genres", "staged_title_cast", "staged_title_providers"]:
            cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
            staged_counts[tbl] = [cursor.fetchone()[0]]
        st.dataframe(pd.DataFrame(staged_counts), use_container_width=True)

    # Reseed option
    st.markdown("---")
    st.markdown("### ⚠️ Danger Zone")
    st.caption("Clears database tables and resets schemas to the default mock dataset.")
    if st.button("🚨 Reset & Reseed Database Schema"):
        init_db(force_reseed=True)
        st.success("Database has been reset and seeded to defaults!")
        st.rerun()
