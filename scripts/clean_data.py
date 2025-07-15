import pandas as pd

def clean_movies():
    mdf = pd.read_csv('./data/movies.csv')
    
    # Remove movies with no genres
    mdf = mdf[mdf['genres'] != "(no genres listed)"]

    # Drop duplicates
    mdf = mdf.drop_duplicates(subset=['movieId'])

    mdf.to_csv("./data/clean/movies_cleaned.csv", index=False)

def clean_ratings():
    rdf = pd.read_csv("./data/ratings.csv")

    # Remove any null values
    rdf = rdf.dropna(subset=["userId", "movieId", "rating", "timestamp"])

    # Convert Types
    rdf['userId'] = rdf['userId'].astype(int)
    rdf['movieId'] = rdf['movieId'].astype(int)
    rdf['rating'] = rdf['rating'].astype(float)
    rdf['timestamp'] = rdf['timestamp'].astype(int)

    rdf = rdf[(rdf['rating'] >= 0) & (rdf['rating'] <= 5)]

    # Keep Latest if duplicates found
    rdf = rdf.sort_values('timestamp').drop_duplicates(subset=['userId', 'movieId'], keep='last')

    rdf.to_csv('./data/clean/ratings_cleaned.csv', index=False)

def clean_tags():
    tags = pd.read_csv('./data/tags.csv')

    # Drop rows with nulls
    tags = tags.dropna(subset=['userId', 'movieId', 'tag', 'timestamp'])

    # Strip spaces in tags
    tags['tag'] = tags['tag'].str.strip()

    # Remove blank tags
    tags = tags[tags['tag'] != '']

    # Convert types
    tags['userId'] = tags['userId'].astype(int)
    tags['movieId'] = tags['movieId'].astype(int)
    tags['timestamp'] = tags['timestamp'].astype(int)

    # Drop duplicates of (userId, movieId, tag)
    tags = tags.drop_duplicates(subset=['userId', 'movieId', 'tag'])

    tags.to_csv('./data/clean/tags_cleaned.csv', index=False)

def clean_links():
    links = pd.read_csv('./data/links.csv')

    # Drop rows with nulls
    links = links.dropna(subset=['movieId', 'imdbId', 'tmdbId'])

    # Convert types
    links['movieId'] = links['movieId'].astype(int)
    links['imdbId'] = links['imdbId'].astype(int)
    links['tmdbId'] = links['tmdbId'].astype(int)

    # Remove Duplicates 
    links = links.drop_duplicates(subset=['movieId', 'imdbId', 'tmdbId'], keep='first')

    links.to_csv('./data/clean/links_cleaned.csv')

if __name__ == '__main__':
    clean_movies()
    clean_ratings()
    clean_tags()
    clean_links()