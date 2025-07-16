import argparse
import logging
from neo4j import GraphDatabase
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Neo4j connection details
uri = "bolt://localhost:7687"
user = "neo4j"
password = "password"

# Initialize Neo4j driver
driver = GraphDatabase.driver(uri, auth=(user, password))

def get_collaborative_recommendations(tx, userId, limit=10):
    """Generate collaborative filtering recommendations with explainable paths."""
    try:
        result = tx.run(
            """
            MATCH path = (u1:User {userId: $userId})-[:RATED]->(m:Movie)<-[:RATED]-(u2:User)-[r:RATED]->(rec:Movie)
            WHERE NOT (u1)-[:RATED]->(rec)
            WITH rec, AVG(toFloat(r.rating)) AS avg_rating, COUNT(DISTINCT u2) AS common_count, 
                 AVG(toFloat(r.rating)) * log10(COUNT(DISTINCT u2)) AS score, 
                 COLLECT(DISTINCT path)[0..3] AS paths
            RETURN rec.movieId AS movieId, rec.title AS title, avg_rating, common_count, score, 
                   paths
            ORDER BY score DESC
            LIMIT $limit
            """,
            userId=userId,
            limit=limit
        )
        records = []
        for record in result:
            path_descriptions = []
            for path in record["paths"]:
                nodes = path.nodes
                relationships = path.relationships
                user2_id = nodes[2]["userId"]
                shared_movie = nodes[1]["title"]
                rating = relationships[2]["rating"]
                path_desc = f"User {user2_id} rated '{shared_movie}' and gave '{record['title']}' a {rating}/5"
                path_descriptions.append(path_desc)
            record_data = record.data()
            record_data["path_descriptions"] = path_descriptions
            records.append(record_data)
        if not records:
            logger.warning(f"No collaborative recommendations found for userId {userId}")
            return []
        return records
    except Exception as e:
        logger.error(f"Query failed for userId {userId}: {e}")
        return []

def recommend_by_genres_tags(tx, userId, limit=10):
    """Recommend movies based on overlapping genres and tags."""
    try:
        result = tx.run(
            """
            WITH datetime().epochSeconds AS now
            MATCH (u:User {userId: $userId})-[:RATED]->(m:Movie)
            OPTIONAL MATCH genre_path = (m)-[:HAS_GENRE]->(g:Genre)
            OPTIONAL MATCH tag_path = (u)-[t:TAGGED]->(m)
            WITH u, COLLECT(DISTINCT g.name) AS userGenres, COLLECT(DISTINCT t.tag) AS userTags, 
                 COLLECT(DISTINCT genre_path)[0..3] AS genre_paths, 
                 COLLECT(DISTINCT tag_path)[0..3] AS tag_paths, now
            MATCH (candidate:Movie)
            WHERE NOT (u)-[:RATED]->(candidate) AND EXISTS((candidate)-[:HAS_GENRE]->(:Genre))
            OPTIONAL MATCH candidate_genre_path = (candidate)-[:HAS_GENRE]->(cg:Genre)
            OPTIONAL MATCH tag_rel_path = (other:User)-[tagRel:TAGGED]->(candidate)
            WITH u, candidate, 
                 COLLECT(DISTINCT cg.name) AS candidateGenres, 
                 COLLECT(DISTINCT tagRel.tag) AS candidateTags,
                 userGenres, userTags, genre_paths, tag_paths, 
                 COLLECT(DISTINCT candidate_genre_path)[0..3] AS candidate_genre_paths,
                 COLLECT(DISTINCT tag_rel_path)[0..3] AS tag_rel_paths, now
            WITH candidate, 
                 [genre IN userGenres WHERE genre IN candidateGenres] AS overlappingGenres,
                 [tag IN userTags WHERE tag IN candidateTags] AS overlappingTags,
                 genre_paths, tag_paths, candidate_genre_paths, tag_rel_paths, now
            WHERE size(overlappingGenres) > 0 OR size(overlappingTags) > 0
            OPTIONAL MATCH rating_path = (other:User)-[r:RATED]->(candidate)
            WITH candidate, overlappingGenres, overlappingTags,
                 COALESCE(AVG(toFloat(r.rating)), 0.0) AS avgRating,
                 COUNT(r) AS ratingCount,
                 COALESCE(AVG(toFloat(r.rating)) * log10(COUNT(r) + 1), 0.0) AS baseScore,
                 COALESCE(AVG(1000.0 / (now - toInteger(r.timestamp) + 1)), 0.0) AS recencyBoost,
                 genre_paths, tag_paths, candidate_genre_paths, tag_rel_paths,
                 COLLECT(DISTINCT rating_path)[0..3] AS rating_paths
            RETURN candidate.movieId AS movieId,
                   candidate.title AS title,
                   overlappingGenres,
                   overlappingTags,
                   avgRating,
                   ratingCount,
                   baseScore,
                   recencyBoost,
                   genre_paths,
                   tag_paths,
                   candidate_genre_paths,
                   tag_rel_paths,
                   rating_paths,
                   (0.6 * baseScore + 0.6 * recencyBoost + 0.4 * size(overlappingGenres) + 0.2 * size(overlappingTags)) AS finalScore
            ORDER BY finalScore DESC
            LIMIT $limit
            """,
            userId=userId,
            limit=limit
        )
        recommendations = []
        for record in result:
            rec = record.data()
            path_descriptions = {
                "genre_paths": [],
                "tag_paths": [],
                "candidate_genre_paths": [],
                "tag_rel_paths": [],
                "rating_paths": []
            }
            for path in record["genre_paths"]:
                nodes = path.nodes
                movie_title = nodes[0]["title"]
                genre_name = nodes[1]["name"]
                path_descriptions["genre_paths"].append(f"User rated '{movie_title}' with genre '{genre_name}'")
            for path in record["tag_paths"]:
                nodes = path.nodes
                movie_title = nodes[1]["title"]
                tag = path.relationships[0]["tag"]
                path_descriptions["tag_paths"].append(f"User tagged '{movie_title}' with '{tag}'")
            for path in record["candidate_genre_paths"]:
                nodes = path.nodes
                genre_name = nodes[1]["name"]
                path_descriptions["candidate_genre_paths"].append(f"Candidate has genre '{genre_name}'")
            for path in record["tag_rel_paths"]:
                nodes = path.nodes
                other_user_id = nodes[0]["userId"]
                tag = path.relationships[0]["tag"]
                path_descriptions["tag_rel_paths"].append(f"User {other_user_id} tagged candidate with '{tag}'")
            for path in record["rating_paths"]:
                nodes = path.nodes
                other_user_id = nodes[0]["userId"]
                rating = path.relationships[0]["rating"]
                path_descriptions["rating_paths"].append(f"User {other_user_id} rated candidate {rating}/5")
            rec["explanations"] = {
                "matched_genres": rec.get("overlappingGenres", []),
                "matched_tags": rec.get("overlappingTags", []),
                "path_descriptions": path_descriptions
            }
            recommendations.append(rec)
        if not recommendations:
            logger.warning(f"No hybrid recommendations found for userId {userId}")
        return recommendations
    except Exception as e:
        logger.error(f"Contextual recommendation failed for userId {userId}: {e}")
        return []

def recommend_by_movie_ids(tx, movie_ids, limit=10):
    """Recommend movies based on a list of movieIds using collaborative filtering."""
    try:
        result = tx.run(
            """
            MATCH (m:Movie)
            WHERE m.movieId IN $movie_ids
            MATCH path = (m)<-[:RATED]-(u:User)-[r:RATED]->(rec:Movie)
            WHERE NOT rec.movieId IN $movie_ids
            WITH rec, AVG(toFloat(r.rating)) AS avg_rating, COUNT(DISTINCT u) AS common_count, 
                 AVG(toFloat(r.rating)) * log10(COUNT(DISTINCT u) + 1) AS score, 
                 COLLECT(DISTINCT path)[0..3] AS paths
            RETURN rec.movieId AS movieId, rec.title AS title, avg_rating, common_count, score, 
                   paths
            ORDER BY score DESC
            LIMIT $limit
            """,
            movie_ids=movie_ids,
            limit=limit
        )
        records = []
        for record in result:
            path_descriptions = []
            for path in record["paths"]:
                nodes = path.nodes
                user_id = nodes[1]["userId"]
                shared_movie = nodes[0]["title"]
                rating = path.relationships[1]["rating"]
                path_desc = f"User {user_id} rated '{shared_movie}' and gave '{record['title']}' a {rating}/5"
                path_descriptions.append(path_desc)
            record_data = record.data()
            record_data["path_descriptions"] = path_descriptions
            records.append(record_data)
        if not records:
            logger.warning(f"No recommendations found for movieIds {movie_ids}")
            return []
        return records
    except Exception as e:
        logger.error(f"Recommendation failed for movieIds {movie_ids}: {e}")
        return []

def print_recommendations(recommendations, rec_type):
    """Print recommendations in a formatted way."""
    if not recommendations:
        print(f"No {rec_type} recommendations found.")
        return
    print(f"\n{rec_type} Recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['title']} (MovieID: {rec['movieId']})")
        if rec_type == "Collaborative":
            print(f"  Average Rating: {rec['avg_rating']:.2f}/5")
            print(f"  Common Users: {rec['common_count']}")
            print(f"  Score: {rec['score']:.2f}")
            print("  Explanation:")
            for path in rec["path_descriptions"]:
                print(f"    - {path}")
        elif rec_type == "Genre/Tag-Based":
            print(f"  Average Rating: {rec['avgRating']:.2f}/5")
            print(f"  Rating Count: {rec['ratingCount']}")
            print(f"  Final Score: {rec['finalScore']:.2f}")
            print(f"  Matched Genres: {', '.join(rec['explanations']['matched_genres'])}")
            print(f"  Matched Tags: {', '.join(rec['explanations']['matched_tags'])}")
            print("  Explanation:")
            for path_type, paths in rec["explanations"]["path_descriptions"].items():
                for path in paths:
                    print(f"    - {path}")
        elif rec_type == "Movie ID-Based":
            print(f"  Average Rating: {rec['avg_rating']:.2f}/5")
            print(f"  Common Users: {rec['common_count']}")
            print(f"  Score: {rec['score']:.2f}")
            print("  Explanation:")
            for path in rec["path_descriptions"]:
                print(f"    - {path}")

def main():
    parser = argparse.ArgumentParser(description="Movie Recommendation System CLI")
    parser.add_argument("--type", choices=["collaborative", "genre", "movie"], default="collaborative",
                        help="Type of recommendation (collaborative, genre, movie)")
    parser.add_argument("--user-id", type=int, help="User ID for recommendations")
    parser.add_argument("--movie-ids", type=str, help="Comma-separated movie IDs (for movie-based recommendations)")
    parser.add_argument("--limit", type=int, default=10, help="Number of recommendations to return")
    args = parser.parse_args()

    def interactive_loop():
        while True:
            print("\nMovie Recommendation System")
            print("1. Collaborative Filtering (User-based)")
            print("2. Genre/Tag-based Recommendations")
            print("3. Movie ID-based Recommendations")
            print("4. Exit")
            choice = input("Select an option (1-4): ")

            if choice == "4":
                print("Exiting...")
                break

            if choice not in ["1", "2", "3"]:
                print("Invalid choice. Please select 1, 2, 3, or 4.")
                continue

            try:
                with driver.session() as session:
                    if choice == "1":
                        user_id = int(input("Enter User ID: "))
                        recommendations = session.execute_read(get_collaborative_recommendations, userId=user_id, limit=args.limit)
                        print_recommendations(recommendations, "Collaborative")
                    elif choice == "2":
                        user_id = int(input("Enter User ID: "))
                        recommendations = session.execute_read(recommend_by_genres_tags, userId=user_id, limit=args.limit)
                        print_recommendations(recommendations, "Genre/Tag-Based")
                    elif choice == "3":
                        movie_ids_input = input("Enter comma-separated Movie IDs (e.g., 82,74,118): ")
                        movie_ids = [int(id.strip()) for id in movie_ids_input.split(",")]
                        recommendations = session.execute_read(recommend_by_movie_ids, movie_ids=movie_ids, limit=args.limit)
                        print_recommendations(recommendations, "Movie ID-Based")
            except Exception as e:
                logger.error(f"Error in interactive loop: {e}")
                print(f"An error occurred: {e}")

    # Check if arguments were provided for non-interactive mode
    if args.user_id or args.movie_ids:
        try:
            with driver.session() as session:
                if args.type == "collaborative" and args.user_id:
                    recommendations = session.execute_read(get_collaborative_recommendations, userId=args.user_id, limit=args.limit)
                    print_recommendations(recommendations, "Collaborative")
                elif args.type == "genre" and args.user_id:
                    recommendations = session.execute_read(recommend_by_genres_tags, userId=args.user_id, limit=args.limit)
                    print_recommendations(recommendations, "Genre/Tag-Based")
                elif args.type == "movie" and args.movie_ids:
                    movie_ids = [int(id.strip()) for id in args.movie_ids.split(",")]
                    recommendations = session.execute_read(recommend_by_movie_ids, movie_ids=movie_ids, limit=args.limit)
                    print_recommendations(recommendations, "Movie ID-Based")
                else:
                    print("Invalid arguments. Use --help for usage details.")
        except Exception as e:
            logger.error(f"Error in non-interactive mode: {e}")
            print(f"An error occurred: {e}")
    else:
        interactive_loop()

    driver.close()

if __name__ == "__main__":
    main()