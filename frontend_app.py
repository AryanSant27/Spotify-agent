import streamlit as st
import requests
import webbrowser

# Backend URL
if "STREAMLIT_URL" in os.environ:
    # Running on Streamlit Cloud, so use the public URL of the backend
    BACKEND_URL = "https://spotify-agent.onrender.com"
else:
    # Running locally, so use the local address of the backend
    BACKEND_URL = "http://127.0.0.1:5000"

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

    if 'token' not in st.session_state:
        login_url = f"{BACKEND_URL}/login"
        st.markdown(f'<a href="{login_url}" target="_self">Login with Spotify</a>', unsafe_allow_html=True)

        # Check for token in URL, set it in session state, and trigger a rerun
        query_params = st.query_params
        if "token" in query_params:
            st.session_state.token = query_params["token"]
            st.rerun() # Use st.rerun to force a script rerun
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