def recommend_by_movie_ids(tx, movie_ids, limit=10):
    """Recommend movies based on a list of movieIds using collaborative filtering."""
    print('Executing query ...')
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
            print(f"No recommendations found for movieIds {movie_ids}")
            return []
        
        return records
    except Exception as e:
        print(f"Recommendation failed for movieIds {movie_ids}: {e}")
        return []
