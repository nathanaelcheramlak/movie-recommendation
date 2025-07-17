import os
import random
from neo4j import GraphDatabase
from dotenv import load_dotenv

from scripts.utils import print_recommendations
from engine.collaborative_recommendations import get_collaborative_recommendations
from engine.context_recommendation import get_context_recommendations
from engine.additional_recommendation import recommend_by_movie_ids
from engine.new_user_recommendation import manage_user

load_dotenv()

# Neo4j connection details
uri = os.getenv('DB_URI')
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')

if not uri or not user or not password:
    raise ValueError('Missing Environment Variables')

# Initialize Neo4j driver
driver = GraphDatabase.driver(uri, auth=(user, password))

def main():
    while True:
        print("\nMovie Recommendation System")
        print("1. User Management")
        print("2. Collaborative Filtering (User-based)")
        print("3. Genre/Tag-based Recommendations")
        print("4. Movie ID-based Recommendations")
        print("5. Exit")
        choice = input("Select an option (1-5): ")

        if choice == "5":
            print("Exiting...")
            break

        if choice not in ["1", "2", "3", "4"]:
            print("Invalid choice. Please select 1, 2, 3, or 4.")
            continue

        try:
            with driver.session() as session:
                if choice == "1":
                    manage_user(session)
                elif choice == "2":
                    user_id = int(input("Enter User ID: "))
                    recommendations = session.execute_read(get_collaborative_recommendations, userId=user_id)
                    print_recommendations(recommendations, "Collaborative")
                elif choice == "3":
                    user_id = int(input("Enter User ID: "))
                    recommendations = session.execute_read(get_context_recommendations, userId=user_id)
                    print_recommendations(recommendations, "Genre/Tag-Based")
                elif choice == "4":
                    movie_ids_input = input("Enter comma-separated Movie IDs (e.g., 82,74,118): ")
                    movie_ids = [int(id.strip()) for id in movie_ids_input.split(",")]
                    recommendations = session.execute_read(recommend_by_movie_ids, movie_ids=movie_ids)
                    print_recommendations(recommendations, "Movie ID-Based")
        except Exception as e:
            print(f"Error in interactive loop: {e}")
            print(f"An error occurred: {e}")

    driver.close()

if __name__ == "__main__":
    main()