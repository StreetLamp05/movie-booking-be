import requests
import json

# --- Configuration ---
API_URL = "http://localhost:5000/api/v1/movies"
MOVIES_FILE = "movies.json"
HEADERS = {"Content-Type": "application/json"}

def post_movies():
    """
    Reads movies from a file and posts them to the API.
    Each line in the file should be a separate JSON object.
    """
    print(f"--- Starting to post movies from {MOVIES_FILE} to {API_URL} ---")
    
    try:
        with open(MOVIES_FILE, 'r') as f:
            for line_num, line in enumerate(f, 1):
                # Skip any blank or empty lines
                if not line.strip():
                    continue

                try:
                    # Try to load the line as JSON to validate it
                    movie_data = json.loads(line)
                    
                    # Send the POST request
                    print(f"\n[Line {line_num}] Posting movie: {movie_data.get('title', 'N/A')}")
                    response = requests.post(API_URL, headers=HEADERS, data=line.encode('utf-8'))
                    
                    # Check the response from the server
                    if 200 <= response.status_code < 300:
                        print(f"  SUCCESS: Status Code {response.status_code}")
                        # Optionally print the response body from the server
                        # print("  Response:", response.json())
                    else:
                        print(f"  ERROR: Received Status Code {response.status_code}")
                        print(f"  Response Body: {response.text}")

                except json.JSONDecodeError:
                    print(f"\n[Line {line_num}] ERROR: Invalid JSON format. Skipping line.")
                    print(f"  Problematic line: {line.strip()}")
                except requests.exceptions.RequestException as e:
                    print(f"\n[Line {line_num}] ERROR: A connection error occurred.")
                    print(f"  Details: {e}")

    except FileNotFoundError:
        print(f"ERROR: The file '{MOVIES_FILE}' was not found in this directory.")
    
    print("\n--- Script finished. ---")

if __name__ == "__main__":
    post_movies()
