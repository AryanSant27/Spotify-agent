
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai
import sqlite3
from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS

app = Flask(__name__)
# For deployment, you'll need to set the frontend URL in your Render environment variables
# e.g., FRONTEND_URL=https://your-frontend-app.netlify.app
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
CORS(app, supports_credentials=True, origins=[FRONTEND_URL]) # Enable CORS for all routes and support credentials

# For production, set this as an environment variable in Render
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'super_secret_dev_key') 

DATABASE_FILE = 'spotify_data.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row # This allows us to access columns by name
    return conn

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS listening_history (
                played_at TEXT PRIMARY KEY,
                artist_name TEXT NOT NULL,
                track_name TEXT NOT NULL,
                album_name TEXT NOT NULL
            )
        ''

        conn.commit()

def get_spotify_oauth():
    load_dotenv()
    return SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope="user-read-recently-played",
        cache_path=None # Disable caching to prevent automatic re-login
    )

def get_spotify_data():
    """Fetches recently played tracks from Spotify and saves them to the database."""
    sp_oauth = get_spotify_oauth()
    token_info = session.get('token_info', None)

    if not token_info:
        return False, "No token info found. Please log in."

    # Check if token is expired and refresh if needed
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info

    sp = spotipy.Spotify(auth=token_info['access_token'])

    try:
        results = sp.current_user_recently_played(limit=50)
    except Exception as e:
        print(f"Error fetching data from Spotify: {e}")
        return False, str(e)

    if not results or not results["items"]:
        print("No recently played tracks found.")
        return False, "No recently played tracks found."

    tracks_added = 0
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for item in results["items"]:
            track = item["track"]
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO listening_history (played_at, artist_name, track_name, album_name)
                    VALUES (?, ?, ?, ?)
                ''',
                (
                    item["played_at"],
                    track["artists"][0]["name"],
                    track["name"],
                    track["album"]["name"],
                ))
                if cursor.rowcount > 0:
                    tracks_added += 1
            except sqlite3.IntegrityError:
                # This means the played_at (PRIMARY KEY) already exists, so it was ignored
                pass
        conn.commit()

    print(f"Successfully added {tracks_added} new tracks to the database.")
    return True, f"Successfully added {tracks_added} new tracks to the database."

def get_sql_from_natural_language(query, conn):
    """Converts natural language query to SQL query using Gemini API."""
    with open("gemini_api_key.txt", "r") as f:
        api_key = f.read().strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in gemini_api_key.txt file.")
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel("gemini-1.5-flash")

    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(listening_history)")
    schema = cursor.fetchall()
    column_names = [row[1] for row in schema]

    prompt = "You have a SQLite table named 'listening_history' with the following columns: " + ', '.join(column_names) + ".\n"
    prompt += "Write a single, valid SQLite query to answer the following user question.\n"
    prompt += "Only return the SQL query itself, with no explanation or markdown.\n\n"
    prompt += "User Question: " + query

    try:
        response = model.generate_content(prompt)
        sql_query = response.text.strip().replace("```sql", "").replace("```", "")
        return sql_query
    except Exception as e:
        print(f"Error generating SQL query: {e}")
        return None

@app.route('/login')
def login():
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    print(f"Generated Spotify Auth URL: {auth_url}")
    return redirect(auth_url)

@app.route('/callback')
def callback():
    sp_oauth = get_spotify_oauth()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    # Redirect back to the frontend application using the FRONTEND_URL env var
    return redirect(f'{FRONTEND_URL}/?loggedIn=true') 

@app.route('/logout')
def logout():
    session.pop('token_info', None)
    return jsonify({"status": "success", "message": "Logged out."})

@app.route('/check_session')
def check_session():
    if 'token_info' in session:
        return jsonify({"status": "logged_in"}), 200
    else:
        return jsonify({"status": "logged_out"}), 401

@app.route('/fetch_data', methods=['POST'])
def fetch_data():
    success, message = get_spotify_data()
    if success:
        return jsonify({"status": "success", "message": message})
    else:
        return jsonify({"status": "error", "message": message}), 500

@app.route('/query', methods=['POST'])
def query_data():
    data = request.get_json()
    natural_language_query = data.get('query')

    if not natural_language_query:
        return jsonify({"status": "error", "message": "No query provided."}), 400

    try:
        with get_db_connection() as conn:
            sql_query = get_sql_from_natural_language(natural_language_query, conn)

            if sql_query:
                try:
                    result_df = pd.read_sql_query(sql_query, conn)
                    return jsonify({"status": "success", "sql_query": sql_query, "result": result_df.to_dict(orient='records')})
                except Exception as e:
                    return jsonify({"status": "error", "message": f"Error executing SQL query: {str(e)}", "sql_query": sql_query}), 500
            else:
                return jsonify({"status": "error", "message": "Could not generate SQL query."}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"Database error: {str(e)}"}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
