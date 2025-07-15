from neo4j import GraphDatabase
import pandas as pd

uri = "bolt://localhost:7687"
user = "neo4j"
password = "password"

driver = GraphDatabase.driver(uri, auth=(user, password))

# Load cleaned CSVs
movies = pd.read_csv('./data/clean/movies_cleaned.csv')
ratings = pd.read_csv('./data/clean/ratings_cleaned.csv')
tags = pd.read_csv('./data/clean/tags_cleaned.csv')
links = pd.read_csv('./data/clean/links_cleaned.csv')

# --- Cypher Loaders ---

def load_movies(tx, movieId, title, genres):
    tx.run(
        """
        MERGE (m:Movie {movieId: $movieId})
          ON CREATE SET m.title = $title
        WITH m, $genres AS genres
        UNWIND genres AS genreName
          MERGE (g:Genre {name: genreName})
          MERGE (m)-[:HAS_GENRE]->(g)
        """,
        movieId=movieId,
        title=title,
        genres=genres
    )

def load_ratings(tx, userId, movieId, rating, timestamp):
    tx.run(
        """
        MERGE (u:User {userId: $userId})
        MERGE (m:Movie {movieId: $movieId})
        MERGE (u)-[:RATED {rating: $rating, timestamp: $timestamp}]->(m)
        """,
        userId=userId,
        movieId=movieId,
        rating=rating,
        timestamp=timestamp
    )

def load_tags(tx, userId, movieId, tag, timestamp):
    tx.run(
        """
        MERGE (u:User {userId: $userId})
        MERGE (m:Movie {movieId: $movieId})
        MERGE (u)-[:TAGGED {tag: $tag, timestamp: $timestamp}]->(m)
        """,
        userId=userId,
        movieId=movieId,
        tag=tag,
        timestamp=timestamp
    )

def load_links(tx, movieId, imdbId, tmdbId):
    tx.run(
        """
        MERGE (m:Movie {movieId: $movieId})
        MERGE (m)-[hl:HAS_LINK]->()
        SET hl.imdbId = $imdbId, hl.tmdbId = $tmdbId
        """,
        movieId=movieId,
        imdbId=imdbId,
        tmdbId=tmdbId
    )

# --- Upload All Data ---

with driver.session() as session:
    # Upload Movies
    for i, row in movies.iterrows():
        genres_list = [g.strip() for g in row['genres'].split('|')]
        session.execute_write(load_movies, int(row['movieId']), row['title'], genres_list)
        print(f"Movie {i+1}/{len(movies)} loaded.")

    # Upload Ratings
    for i, row in ratings.iterrows():
        session.execute_write(load_ratings, int(row['userId']), int(row['movieId']), float(row['rating']), int(row['timestamp']))
        print(f"Rating {i+1}/{len(ratings)} loaded.")

    # Upload Tags
    for i, row in tags.iterrows():
        session.execute_write(load_tags, int(row['userId']), int(row['movieId']), row['tag'], int(row['timestamp']))
        print(f"Tag {i+1}/{len(tags)} loaded.")

    # Upload Links
    for i, row in links.iterrows():
        session.execute_write(load_links, int(row['movieId']), int(row['imdbId']), int(row['tmdbId']))
        print(f"Link {i+1}/{len(links)} loaded.")

driver.close()
