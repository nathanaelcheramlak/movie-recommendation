import random

def create_new_user(tx):
    """Generate a random unique user ID and create a new user node."""
    while True:
        new_user_id = random.randint(1000, 9999)
        result = tx.run("MATCH (u:User {userId: $user_id}) RETURN u", user_id=new_user_id)
        if not result.single():  # If no user with this ID exists
            tx.run("CREATE (u:User {userId: $user_id})", user_id=new_user_id)
            return new_user_id

def add_liked_movie(tx, user_id, movie_id):
    """Add a liked movie for a user."""
    query = """
    MATCH (u:User {userId: $user_id})
    MATCH (m:Movie {movieId: $movie_id})
    MERGE (u)-[:LIKES]->(m)
    RETURN m
    """
    result = tx.run(query, user_id=user_id, movie_id=movie_id)
    return result.single()

def remove_liked_movie(tx, user_id, movie_id):
    """Remove a liked movie for a user."""
    query = """
    MATCH (u:User {userId: $user_id})-[r:LIKES]->(m:Movie {movieId: $movie_id})
    DELETE r
    """
    tx.run(query, user_id=user_id, movie_id=movie_id)

def get_liked_movies(tx, user_id):
    """Get all liked movies for a user."""
    query = """
    MATCH (u:User {userId: $user_id})-[:LIKES]->(m:Movie)
    RETURN m.movieId AS movieId, m.title AS title
    """
    result = tx.run(query, user_id=user_id)
    return [record.data() for record in result]

def print_liked_movies(liked_movies):
    """Print liked movies in a formatted way."""
    if not liked_movies:
        print("\nNo liked movies found.")
        return
    print("\nLiked Movies:")
    for i, movie in enumerate(liked_movies, 1):
        print(f"{i}. {movie['title']} (MovieID: {movie['movieId']})")

def manage_user(session):
    """Sub-menu for user management including liked movies."""
    while True:
        print("\nUser Management")
        print("1. Create New User")
        print("2. Add Liked Movie")
        print("3. Remove Liked Movie")
        print("4. List Liked Movies")
        print("5. Back to Main Menu")
        sub_choice = input("Select an option (1-5): ")

        if sub_choice == "5":
            print("Returning to main menu...")
            break

        if sub_choice not in ["1", "2", "3", "4"]:
            print("Invalid choice. Please select 1, 2, 3, 4, or 5.")
            continue

        try:
            if sub_choice == "1":
                new_user_id = session.execute_write(create_new_user)
                print(f"New user created with ID: {new_user_id}")
            elif sub_choice == "2":
                user_id = int(input("Enter User ID: "))
                movie_id = int(input("Enter Movie ID to like: "))
                session.execute_write(add_liked_movie, user_id, movie_id)
                print(f"Added Movie ID {movie_id} to liked movies for User ID {user_id}")
            elif sub_choice == "3":
                user_id = int(input("Enter User ID: "))
                movie_id = int(input("Enter Movie ID to unlike: "))
                session.execute_write(remove_liked_movie, user_id, movie_id)
                print(f"Removed Movie ID {movie_id} from liked movies for User ID {user_id}")
            elif sub_choice == "4":
                user_id = int(input("Enter User ID: "))
                liked_movies = session.execute_read(get_liked_movies, user_id)
                print_liked_movies(liked_movies)
        except Exception as e:
            print(f"Error in user management: {e}")
            print(f"An error occurred: {e}")