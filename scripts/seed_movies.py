"""
    POST /api/v1/movies
    Body:
    {
      "title": "Inception",
      "cast": "...",
      "director": "...",
      "producer": "...",
      "synopsis": "...",
      "trailer_picture": "https://.../cover.jpg",
      "video": "https://.../movie.mp4",
      "film_rating_code": "PG-13",
      "categories": ["Sci-Fi", "Thriller"]          # optional
      # or categories_ids: [1, 2]                   # optional
    }
"""

import csv, os, json, requests

api_base = os.getenv("BACKEND_POINT", "http://localhost:5000/")
if not api_base.endswith('/'):
    api_base += '/'
api_url = f"{api_base}api/v1/movies"

def seed_movies() -> None:
    success = 0
    failed = 0
    
    with open('movies.csv', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            status_code = seed_movie(row)
            if status_code in [200, 201]:
                success += 1
            else:
                failed += 1

    print(f"Success: {success}, Failed: {failed}")

def seed_movie(row: dict) -> int:
    try:
        categories = json.loads(row.get('categories', '[]'))
        
        payload = {
            "title": row.get('title'),
            "cast": row.get('cast'),
            "director": row.get('director'),
            "producer": row.get('producer'),
            "synopsis": row.get('synopsis'),
            "trailer_picture": row.get('trailer_picture'),
            "video": row.get('video'),
            "film_rating_code": row.get('film_rating_code'),
            "categories": categories
        }
        
        response = requests.post(api_url, json=payload)
        
        if response.status_code not in [200, 201]:
            print(f"failed seeding: '{payload['title']}': {response.status_code} - {response.text}")
            
        return response.status_code
    except Exception as e:
        print(f"error in row {row.get('title')}: {e}")
        return 500

if __name__ == "__main__":
    seed_movies()