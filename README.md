# 🎬 Neo4j Movie Recommendation System

This is a minimal, modular recommendation system for movies, powered by Neo4j. It supports collaborative filtering, content-based (genre/tag) recommendations, and hybrid methods with explainable paths.


## 🚀 Features

✅ Collaborative filtering with user-user similarities.  
✅ Contextual / content-based recommendations using genres and tags.   
✅ Clean CSV data loader for Neo4j.  
✅ Logging and error handling throughout.


## ⚙️ Setup

1️⃣ Clone the repo:

```bash
git clone https://github.com/nathanaelcheramlak/movie-recommendation
cd movie-recommendation
```

2️⃣ Install dependencies:

```bash
pip install -r requirements.txt
```

3️⃣ Create & Configure your .env:

```ini

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

4️⃣ Start your Neo4j instance and ensure the credentials match.


## 🧩 How It Works
1. **Load Data:**
Ingests CSV data into your Neo4j graph.

2. **Recommendation Engines:**

    * Collaborative: Finds users with similar tastes.

    * Contextual (Genres/Tags): Recommends based on overlapping genres/tags.

    * Movie: Recommends similar movies given a movie id.

3. **Explainable Paths:**
Recommendations include why a movie is suggested (paths in the graph).

## 🏃 Usage
Run all recommendations with:

```bash
python main.py
```

---

Test Neo4j connectivity:

```bash
python test_connection.py
```

## Authors 
Nathanael @ 2025