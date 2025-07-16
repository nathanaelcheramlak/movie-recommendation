def get_collaborative_recommendations(tx, userId, limit=10):
    """Generate collaborative filtering recommendations with explainable paths."""
    print('Executing query ...')
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
        # print(result)
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
            print(f"No collaborative recommendations found for userId {userId}")
            return []
        return records
    except Exception as e:
        print(f"Query failed for userId {userId}: {e}")
        return []