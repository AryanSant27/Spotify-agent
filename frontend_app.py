import streamlit as st
import requests
import webbrowser
import os
from urllib.parse import urlparse

# Determine Backend URL dynamically
if st.runtime.exists():
    # Running on Streamlit Cloud
    # Streamlit Cloud sets STREAMLIT_URL env var, which is the public URL of the app
    if "STREAMLIT_URL" in os.environ:
        parsed_url = urlparse(os.environ["STREAMLIT_URL"])
        # The backend is running on the same host as the frontend, but on port 5000
        BACKEND_URL = f"http://{parsed_url.hostname}:5000"
    else:
        # Fallback for local testing if STREAMLIT_URL is not set in a cloud-like environment
        BACKEND_URL = "http://localhost:5000"
else:
    # Running locally
    BACKEND_URL = "http://localhost:5000"

st.write(f"DEBUG: Backend URL is {BACKEND_URL}") # Debugging line

def query_backend(token, query):
    """Sends a natural language query to the backend and returns the result."""
    headers = {"Authorization": f"Bearer {token}"}
    data = {"query": query}
    response = requests.post(f"{BACKEND_URL}/query", headers=headers, json=data)
    return response.json()

def fetch_and_store_data(token):
    """Triggers the backend to fetch and store Spotify data."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BACKEND_URL}/fetch_data", headers=headers)
    return response.json()

def main():
    """Main function to run the Streamlit app."""
    st.title("Spotify Music Recommender")

    # Get the access token from the URL query parameters
    query_params = st.query_params
    token = query_params.get("token")

    if token:
        st.session_state.token = token

    if "token" not in st.session_state:
        # Use the dynamically determined BACKEND_URL for login
        st.markdown(f"<a href=\"{BACKEND_URL}/login\" target=\"_self\">Login with Spotify</a>", unsafe_allow_html=True)
    else:
        st.success("Successfully logged in!")

        # Button to fetch and store data
        if st.button("Fetch and Store Spotify Data"):
            with st.spinner("Fetching and storing data..."):
                result = fetch_and_store_data(st.session_state.token)
                if result.get("status") == "success":
                    st.success(result.get("message"))
                else:
                    st.error(f"Error: {result.get("message")}")

        st.header("Natural Language Query")
        st.info("Your queries are processed by the backend using AI to generate SQL, which then queries your local Spotify listening history database. Data is fetched from Spotify and stored in the database via the 'Fetch and Store Spotify Data' button.")
        query = st.text_input("Enter your query (e.g., 'Show me my most played artist'):")
        if st.button("Run Query"):
            if query:
                query_result = query_backend(st.session_state.token, query)
                if query_result.get("status") == "success":
                    st.write("**SQL Query:**")
                    st.code(query_result.get("sql_query"))
                    st.write("**Result:**")
                    st.json(query_result.get("result"))
                else:
                    st.error(f"Error: {query_result.get("message")}")
            else:
                st.warning("Please enter a query.")

if __name__ == "__main__":
    main()