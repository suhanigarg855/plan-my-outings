import requests

# API for TMDB : Movie Ratings and Information

# --- Configuration ---
API_KEY = "3277ba2da8ba2bc634d55fe3759b0543" 
BASE_URL = "https://api.themoviedb.org/3"

# --- Function 1: Get Currently Active/Now Playing Movies ---
def get_now_playing_movies():
    """Fetches movies currently in theaters (Now Playing)."""
    endpoint = f"{BASE_URL}/movie/now_playing"
    params = {
        'api_key': API_KEY,
        'language': 'en-US',
        'page': 1,
        # 'region': 'US' # You can uncomment this and change the region for more localized data
    }

    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()
        print("\n--- Now Playing Movies (Active) ---")
        for movie in data.get('results', [])[:5]:
            print(f"- {movie.get('title')} (Release: {movie.get('release_date')}) - Rating: {movie.get('vote_average')}")
        
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# --- Function 2: Get Best-Rated Movies (Discover Endpoint) ---
def get_best_rated_movies(min_rating=7.5, min_votes=1000):
    """
    Fetches movies with high ratings and popularity.
    Simulates the 'best movies based on TMDB' logic.
    """
    endpoint = f"{BASE_URL}/discover/movie"
    params = {
        'api_key': API_KEY,
        'language': 'en-US',
        'sort_by': 'vote_average.desc', # Sort by best rating
        'vote_count.gte': min_votes,     # Only include movies with at least N votes
        'vote_average.gte': min_rating,  # Only include movies with at least N average rating
        'page': 1
    }
    
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        print("\n--- Best Rated Movies ---")
        for movie in data.get('results', [])[:5]:
            print(f"- {movie.get('title')} (Rating: {movie.get('vote_average')}, Votes: {movie.get('vote_count')})")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


# --- Execution ---
# get_now_playing_movies()
# get_best_rated_movies()

# print("\n--- Remember to replace 'xyz' with your actual TMDB API Key! ---")