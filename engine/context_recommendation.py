def get_context_recommendations(tx, userId, limit=10):
    """Recommend movies based on overlapping genres and tags."""
    print('Executing query ...')
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
            print(f"No hybrid recommendations found for userId {userId}")

        return recommendations
    except Exception as e:
        print(f"Contextual recommendation failed for userId {userId}: {e}")
        return []