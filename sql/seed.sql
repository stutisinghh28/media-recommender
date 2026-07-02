-- Seed Genres (TMDB Standard IDs)
INSERT OR REPLACE INTO genres (genre_id, name) VALUES
(28, 'Action'),
(12, 'Adventure'),
(16, 'Animation'),
(35, 'Comedy'),
(80, 'Crime'),
(99, 'Documentary'),
(18, 'Drama'),
(10751, 'Family'),
(14, 'Fantasy'),
(36, 'History'),
(27, 'Horror'),
(10402, 'Music'),
(9648, 'Mystery'),
(10749, 'Romance'),
(878, 'Science Fiction'),
(10770, 'TV Movie'),
(53, 'Thriller'),
(10752, 'War'),
(37, 'Western'),
(10759, 'Action & Adventure'), -- TV Specific
(10762, 'Kids'),
(10763, 'News'),
(10764, 'Reality'),
(10765, 'Sci-Fi & Fantasy'), -- TV Specific
(10766, 'Soap'),
(10767, 'Talk'),
(10768, 'War & Politics');

-- Seed Watch Providers
INSERT OR REPLACE INTO watch_providers (provider_id, provider_name, logo_path) VALUES
(8, 'Netflix', '/p1E68616i62V80QNzpqoMRBECHO.jpg'),
(337, 'Disney Plus', '/9A1q8MK6Z3w74v4TB4ihR6AX5xL.jpg'),
(119, 'Amazon Prime Video', '/h5G0w251Ey5J5y94Lg76sF52j4V.jpg'),
(350, 'Apple TV Plus', '/6nusrfQLpVKuDG47nJ7uV75Q0tV.jpg'),
(15, 'Hulu', '/8bq7JgH46G6JpHtA5fM8U17U5jK.jpg');

-- Seed Mock Users
INSERT OR REPLACE INTO users (user_id, username) VALUES
(1, 'Alice'),
(2, 'Bob'),
(3, 'Charlie'),
(4, 'Diana');

-- Seed User Preferences (Top 4 Genres per User)
-- Alice: Science Fiction (878), Action (28), Adventure (12), Thriller (53)
INSERT OR REPLACE INTO user_preferences (user_id, genre_id, preference_order) VALUES
(1, 878, 1),
(1, 28, 2),
(1, 12, 3),
(1, 53, 4);

-- Bob: Science Fiction (878), Drama (18), Mystery (9648), Sci-Fi & Fantasy (10765)
INSERT OR REPLACE INTO user_preferences (user_id, genre_id, preference_order) VALUES
(2, 878, 1),
(2, 18, 2),
(2, 9648, 3),
(2, 10765, 4);

-- Charlie: Comedy (35), Animation (16), Family (10751), Fantasy (14)
INSERT OR REPLACE INTO user_preferences (user_id, genre_id, preference_order) VALUES
(3, 35, 1),
(3, 16, 2),
(3, 10751, 3),
(3, 14, 4);

-- Diana: Drama (18), Thriller (53), Crime (80), Romance (10749)
INSERT OR REPLACE INTO user_preferences (user_id, genre_id, preference_order) VALUES
(4, 18, 1),
(4, 53, 2),
(4, 80, 3),
(4, 10749, 4);


-- Seed Curated Titles
-- Format: title_id = '{media_type}_{tmdb_id}'
INSERT OR REPLACE INTO titles (title_id, tmdb_id, media_type, title, overview, release_date, rating, vote_count, popularity, poster_path, last_updated) VALUES
('movie_27205', 27205, 'movie', 'Inception', 'Cobb, a skilled thief who steals valuable secrets from deep within the subconscious during the dream state...', '2010-07-15', 8.4, 34000, 85.5, '/o07wMNjCYmIhNavkgbbG781I6mM.jpg', datetime('now')),
('movie_157336', 157336, 'movie', 'Interstellar', 'The adventures of a group of explorers who make use of a newly discovered wormhole to surpass the limitations on human space travel...', '2014-11-05', 8.4, 32000, 145.2, '/gEU2QvH353eGo32vjXCoBG5C3t1.jpg', datetime('now')),
('movie_155', 155, 'movie', 'The Dark Knight', 'Batman raises the stakes in his war on crime. With the help of Lt. Jim Gordon and District Attorney Harvey Dent, Batman sets out to dismantle the remaining criminal organizations that plague the streets...', '2008-07-16', 8.5, 30000, 95.8, '/qJ2tWGB2XclmAEqiNVDHYiB3n9D.jpg', datetime('now')),
('movie_680', 680, 'movie', 'Pulp Fiction', 'A burger-loving hitman, his philosophical partner, a drug-addled gangster''s moll, and a washed-up boxer converge in this sprawling comedic crime caper...', '1994-09-10', 8.5, 26000, 68.3, '/d5i25Cc136t8wZJ62V4BrMK2tKF.jpg', datetime('now')),
('movie_129', 129, 'movie', 'Spirited Away', 'A young girl, Chihiro, becomes trapped in a strange new world of spirits. When her parents undergo a mysterious transformation, she must call upon the courage she never knew she had to free her family...', '2001-07-20', 8.5, 15000, 72.1, '/39wmItIWsg5sclgUjZ7jIUsHB4Y.jpg', datetime('now')),
('movie_496243', 496243, 'movie', 'Parasite', 'All unemployed, Ki-taek''s family takes peculiar interest in the wealthy and glamorous Parks for their livelihood until they get entangled in an unexpected incident...', '2019-05-30', 8.5, 16000, 64.9, '/7IiTTvvCYvi200zN0SOm42agxWN.jpg', datetime('now')),
('movie_603', 603, 'movie', 'The Matrix', 'Set in the 22nd century, The Matrix tells the story of a computer hacker who joins a group of underground insurgents who fight the vast and powerful computers who now rule the earth...', '1999-03-30', 8.2, 24000, 88.4, '/f89U3wzqrjFmZ9S3dtwRfsyR8J1.jpg', datetime('now')),
('movie_299534', 299534, 'movie', 'Avengers: Endgame', 'After the devastating events of Avengers: Infinity War, the universe is in ruins. With the help of remaining allies, the Avengers assemble once more in order to reverse Thanos'' actions and restore balance to the universe...', '2019-04-24', 8.3, 23000, 115.6, '/or065R4vRpqnnIY3h6ehjypaXOH.jpg', datetime('now')),
('movie_24428', 24428, 'movie', 'The Avengers', 'Earth''s mightiest heroes must come together and learn to fight as a team if they are to stop the mischievous Loki and his alien army from enslaving humanity...', '2012-04-25', 7.7, 29000, 82.3, '/RYMX2wc7H6Yv46L2eyq58wJ8GI.jpg', datetime('now')),
('movie_120', 120, 'movie', 'The Lord of the Rings: The Fellowship of the Ring', 'Young hobbit Frodo Baggins, after inheriting a mysterious ring, must leave his home and journey to the fires of Mount Doom to destroy it...', '2001-12-18', 8.4, 23000, 105.4, '/6oom5QDNv285P1w64QI6QIeeRk1.jpg', datetime('now')),
('movie_121', 121, 'movie', 'The Lord of the Rings: The Two Towers', 'Frodo and Sam discover they are being followed by the mysterious Gollum. Meanwhile, Aragorn, Legolas, and Gimli make their way to the kingdom of Rohan...', '2002-12-18', 8.4, 20000, 98.7, '/5VTn0Jym252264g7j21rVCAW6CB.jpg', datetime('now')),
('movie_122', 122, 'movie', 'The Lord of the Rings: The Return of the King', 'Aragorn is revealed as the heir to the ancient kings as he, Gandalf and the other members of the broken fellowship struggle to save Gondor...', '2003-12-17', 8.5, 22000, 112.5, '/rC0w7tIr76vy6q2t75g56d60rvv.jpg', datetime('now')),
('movie_13', 13, 'movie', 'Forrest Gump', 'A man with a low IQ has accomplished great things in his life and been present during significant historic events—in each case, far exceeding what anyone imagined he could do...', '1994-07-06', 8.5, 25000, 84.1, '/arw2gcBzpzw2BbJgJ2R2Z6dj1mY.jpg', datetime('now')),
('movie_238', 238, 'movie', 'The Godfather', 'Spanning the years 1945 to 1955, a chronicle of the fictional Italian-American Corleone crime family. When organized crime family patriarch, Vito Corleone, is barely survives an attempt on his life...', '1972-03-14', 8.7, 19000, 110.3, '/3bhkrj6PMMn799ICwLAyp31SR6e.jpg', datetime('now')),
('movie_278', 278, 'movie', 'The Shawshank Redemption', 'Framed in the 1940s for the double murder of his wife and her lover, upstanding banker Andy Dufresne begins a new life at the Shawshank prison...', '1994-09-23', 8.7, 24000, 120.4, '/ly890kGU59trm743EVxei101ps5.jpg', datetime('now')),
('tv_1396', 1396, 'tv', 'Breaking Bad', 'Walter White, a chemistry teacher, discovers he has cancer and decides to get into the meth-making business to repay his medical debts...', '2008-01-20', 8.9, 12000, 240.1, '/ztkUQLEnPiezoVT6SxRmr6fC25n.jpg', datetime('now')),
('tv_66732', 66732, 'tv', 'Stranger Things', 'When a young boy vanishes, a town uncovers a mystery involving secret experiments, terrifying supernatural forces and one strange little girl...', '2016-07-15', 8.6, 16000, 195.4, '/x270ug41o7j2pa86P6Spu9nd3cT.jpg', datetime('now')),
('tv_1399', 1399, 'tv', 'Game of Thrones', 'Seven noble families fight for control of the mythical land of Westeros. Friction between the houses leads to full-scale war...', '2011-04-17', 8.4, 21000, 280.5, '/1XS1qqmg4QXTCoOIuD1s51VNuOI.jpg', datetime('now')),
('tv_1668', 1668, 'tv', 'Friends', 'Follow the lives of six reckless adults living in Manhattan, as they indulge in adventures which make their lives both troublesome and happening...', '1994-09-22', 8.4, 7000, 150.3, '/jgG3w5hZ8P4n1d2s0F28O17U5jK.jpg', datetime('now')),
('tv_2316', 2316, 'tv', 'The Office', 'The everyday lives of office employees in the Scranton, Pennsylvania branch of the fictional Dunder Mifflin Paper Company...', '2005-03-24', 8.6, 9000, 135.2, '/7cr4xeeR1aR0sS57qVj96rZ44gS.jpg', datetime('now')),
('tv_31917', 31917, 'tv', 'Pretty Little Liars', 'Four friends band together against an anonymous foe who threatens to reveal their darkest secrets, while also investigating the disappearance of their best friend...', '2010-06-08', 8.0, 2000, 45.3, '/vC324HGv2Xn4xPA6P6Spu9nd3cT.jpg', datetime('now'));

-- Seed Title Genre Mappings
-- Inception: Action (28), Adventure (12), Sci-Fi (878)
INSERT OR REPLACE INTO title_genres (title_id, genre_id) VALUES
('movie_27205', 28), ('movie_27205', 12), ('movie_27205', 878),
-- Interstellar: Adventure (12), Drama (18), Sci-Fi (878)
('movie_157336', 12), ('movie_157336', 18), ('movie_157336', 878),
-- The Dark Knight: Action (28), Crime (80), Drama (18), Thriller (53)
('movie_155', 28), ('movie_155', 80), ('movie_155', 18), ('movie_155', 53),
-- Pulp Fiction: Crime (80), Thriller (53)
('movie_680', 80), ('movie_680', 53),
-- Spirited Away: Animation (16), Family (10751), Fantasy (14)
('movie_129', 16), ('movie_129', 10751), ('movie_129', 14),
-- Parasite: Comedy (35), Thriller (53), Drama (18)
('movie_496243', 35), ('movie_496243', 53), ('movie_496243', 18),
-- The Matrix: Action (28), Sci-Fi (878)
('movie_603', 28), ('movie_603', 878),
-- Avengers: Endgame: Action (28), Adventure (12), Sci-Fi (878)
('movie_299534', 28), ('movie_299534', 12), ('movie_299534', 878),
-- The Avengers: Action (28), Adventure (12), Sci-Fi (878)
('movie_24428', 28), ('movie_24428', 12), ('movie_24428', 878),
-- LOTR: Fellowship: Adventure (12), Fantasy (14)
('movie_120', 12), ('movie_120', 14),
-- LOTR: Two Towers: Adventure (12), Fantasy (14)
('movie_121', 12), ('movie_121', 14),
-- LOTR: Return: Adventure (12), Fantasy (14)
('movie_122', 12), ('movie_122', 14),
-- Forrest Gump: Comedy (35), Drama (18), Romance (10749)
('movie_13', 35), ('movie_13', 18), ('movie_13', 10749),
-- The Godfather: Drama (18), Crime (80)
('movie_238', 18), ('movie_238', 80),
-- The Shawshank Redemption: Drama (18), Crime (80)
('movie_278', 18), ('movie_278', 80),
-- Breaking Bad: Drama (18), Crime (80)
('tv_1396', 18), ('tv_1396', 80),
-- Stranger Things: Drama (18), Mystery (9648), Sci-Fi & Fantasy (10765)
('tv_66732', 18), ('tv_66732', 9648), ('tv_66732', 10765),
-- Game of Thrones: Drama (18), Action & Adventure (10759), Sci-Fi & Fantasy (10765)
('tv_1399', 18), ('tv_1399', 10759), ('tv_1399', 10765),
-- Friends: Comedy (35)
('tv_1668', 35),
-- The Office: Comedy (35)
('tv_2316', 35),
-- Pretty Little Liars: Drama (18), Mystery (9648)
('tv_31917', 18), ('tv_31917', 9648);

-- Seed Title Providers
-- Inception: Netflix (8), Disney Plus (337)
INSERT OR REPLACE INTO title_providers (title_id, provider_id, display_priority) VALUES
('movie_27205', 8, 1), ('movie_27205', 337, 2),
-- Interstellar: Amazon Prime (119), Netflix (8)
('movie_157336', 119, 1), ('movie_157336', 8, 2),
-- The Dark Knight: Netflix (8)
('movie_155', 8, 1),
-- Pulp Fiction: Hulu (15)
('movie_680', 15, 1),
-- Spirited Away: Netflix (8)
('movie_129', 8, 1),
-- Parasite: Amazon Prime (119)
('movie_496243', 119, 1),
-- The Matrix: Netflix (8), Amazon Prime (119)
('movie_603', 8, 1), ('movie_603', 119, 2),
-- Breaking Bad: Netflix (8)
('tv_1396', 8, 1),
-- Stranger Things: Netflix (8)
('tv_66732', 8, 1),
-- Game of Thrones: Disney Plus (337)
('tv_1399', 337, 1);

-- Seed Title Cast
-- Inception
INSERT OR REPLACE INTO title_cast (title_id, actor_name, character_name, cast_order) VALUES
('movie_27205', 'Leonardo DiCaprio', 'Cobb', 0),
('movie_27205', 'Joseph Gordon-Levitt', 'Arthur', 1),
('movie_27205', 'Elliot Page', 'Ariadne', 2),
-- Interstellar
('movie_157336', 'Matthew McConaughey', 'Cooper', 0),
('movie_157336', 'Anne Hathaway', 'Brand', 1),
('movie_157336', 'Jessica Chastain', 'Murph', 2),
-- The Dark Knight
('movie_155', 'Christian Bale', 'Bruce Wayne / Batman', 0),
('movie_155', 'Heath Ledger', 'Joker', 1),
('movie_155', 'Gary Oldman', 'Jim Gordon', 2),
-- Breaking Bad
('tv_1396', 'Bryan Cranston', 'Walter White', 0),
('tv_1396', 'Aaron Paul', 'Jesse Pinkman', 1);

-- Seed Watch Histories
-- Alice watched: Inception, The Matrix, The Avengers
INSERT OR REPLACE INTO watch_history (user_id, title_id, watched_at, user_rating) VALUES
(1, 'movie_27205', datetime('now', '-5 days'), 9.0),
(1, 'movie_603', datetime('now', '-2 days'), 8.5),
(1, 'movie_24428', datetime('now', '-10 days'), 7.5);

-- Bob watched: Inception, Interstellar
INSERT OR REPLACE INTO watch_history (user_id, title_id, watched_at, user_rating) VALUES
(2, 'movie_27205', datetime('now', '-12 days'), 9.5),
(2, 'movie_157336', datetime('now', '-1 day'), 8.0);

-- Charlie watched: Spirited Away, Friends
INSERT OR REPLACE INTO watch_history (user_id, title_id, watched_at, user_rating) VALUES
(3, 'movie_129', datetime('now', '-20 days'), 10.0),
(3, 'tv_1668', datetime('now', '-30 days'), 8.0);

-- Diana watched: The Dark Knight, Pulp Fiction, The Godfather
INSERT OR REPLACE INTO watch_history (user_id, title_id, watched_at, user_rating) VALUES
(4, 'movie_155', datetime('now', '-15 days'), 9.0),
(4, 'movie_680', datetime('now', '-8 days'), 8.0),
(4, 'movie_238', datetime('now', '-4 days'), 9.5);
