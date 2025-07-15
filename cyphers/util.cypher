// Constraints
CREATE CONSTRAINT movie_id_unique IF NOT EXISTS
FOR (m:Movie) REQUIRE m.movieId IS UNIQUE;

CREATE CONSTRAINT genre_name_unique IF NOT EXISTS
FOR (g:Genre) REQUIRE g.name IS UNIQUE;

CREATE CONSTRAINT user_id_unique IF NOT EXISTS 
FOR (u:User) REQUIRE u.userId IS UNIQUE;

CREATE CONSTRAINT tag_name_unique IF NOT EXISTS
FOR (t:Tag) REQUIRE t.name IS UNIQUE;

CREATE CONSTRAINT link_imdbId_unique IF NOT EXISTS
FOR (l:Link) REQUIRE l.imdbId IS UNIQUE;


// Indexes
CREATE INDEX FOR (u:User) ON (u.userId);
CREATE INDEX FOR (m:Movie) ON (m.movieId);
CREATE INDEX FOR (g:Genre) ON (g.name);
CREATE INDEX FOR (t:Tag) ON (t.tag);
CREATE INDEX FOR (l:Link) ON (l.movieId);