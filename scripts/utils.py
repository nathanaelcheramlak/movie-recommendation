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