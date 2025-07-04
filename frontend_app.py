import streamlit as st
import requests
import base64

# Backend URL
BACKEND_URL = "http://localhost:5000"

def add_background_logo(logo_path, opacity=0.1, blur_amount=3):
    """
    Adds a background logo with blur effect to the Streamlit app.
    
    Args:
        logo_path (str): Path to the logo image file
        opacity (float): Opacity of the background logo (0.0 to 1.0)
        blur_amount (int): Amount of blur to apply (in pixels)
    """
    try:
        # Read and encode the logo image
        with open(logo_path, "rb") as image_file:
            encoded_logo = base64.b64encode(image_file.read()).decode()
        
        # Create CSS for background logo
        background_logo_css = f"""
        <style>
        /* Background logo with blur effect */
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url("data:image/png;base64,{encoded_logo}");
            background-repeat: no-repeat;
            background-position: center center;
            background-size: 1000px 1000px; /* Adjust size as needed */
            opacity: {opacity};
            filter: blur({blur_amount}px);
            z-index: -1;
            pointer-events: none;
        }}
        </style>
        """
        
        # Apply the CSS
        st.markdown(background_logo_css, unsafe_allow_html=True)
        
    except FileNotFoundError:
        st.error(f"Logo file not found: {logo_path}")
    except Exception as e:
        st.error(f"Error loading background logo: {str(e)}")

def add_background_logo_from_url(logo_url, opacity=0.1, blur_amount=3):
    """
    Adds a background logo from URL with blur effect to the Streamlit app.
    
    Args:
        logo_url (str): URL of the logo image
        opacity (float): Opacity of the background logo (0.0 to 1.0)
        blur_amount (int): Amount of blur to apply (in pixels)
    """
    background_logo_css = f"""
    <style>
    /* Background logo with blur effect */
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: url("{logo_url}");
        background-repeat: no-repeat;
        background-position: center center;
        background-size: 400px 400px; /* Adjust size as needed */
        opacity: {opacity};
        filter: blur({blur_amount}px);
        z-index: -1;
        pointer-events: none;
    }}
    </style>
    """
    
    # Apply the CSS
    st.markdown(background_logo_css, unsafe_allow_html=True)

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
    
    # ADD YOUR BACKGROUND LOGO HERE - REPLACE "spotify_logo.png" WITH YOUR IMAGE PATH
    add_background_logo(r"static/Spotify_Primary_Logo_RGB_Green.png", opacity=0.15, blur_amount=4)
    
    # If you want to use a URL instead, comment the line above and uncomment this:
    # add_background_logo_from_url("https://your-logo-url.com/spotify-logo.png", opacity=0.1, blur_amount=3)
    
    # Custom CSS for background and glass effect
    st.markdown(
        """
        <style>
        /* Overall app background with a subtle pattern */
        .stApp {
            background-color: #121212; /* Dark background */
            background-image: linear-gradient(45deg, rgba(255,255,255,.05) 25%, transparent 25%, transparent 75%, rgba(255,255,255,.05) 75%, rgba(255,255,255,.05) 100%);
            background-size: 20px 20px;
            background-attachment: fixed;
            filter: none; /* Ensure no blur is applied to the app container itself */
        }

        /* Glass effect for the main content area */
        .main .block-container {
            background-color: rgba(38, 38, 38, 0.8); /* Semi-transparent secondary background */
            border-radius: 15px; /* Slightly more rounded corners */
            padding: 2.5rem; /* Increased padding */
            backdrop-filter: blur(15px); /* Stronger blur for more noticeable glass effect */
            -webkit-backdrop-filter: blur(15px); /* For Safari */
            border: 1px solid rgba(255, 255, 255, 0.15); /* More visible border */
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2); /* More pronounced shadow */
            margin-top: 2rem; /* Add some top margin */
            margin-bottom: 2rem; /* Add some bottom margin */
            filter: none; /* Ensure no blur is applied to the content block itself */
        }

        /* Adjust text color for better contrast on blurred background */
        h1, h2, h3, h4, h5, h6, p, .stMarkdown, .stText, .stCode, label {
            color: #FFFFFF; /* Ensure text is white */
        }

        /* Adjust button colors to match theme */
        .stButton>button {
            background-color: #1ED760;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 12px 25px;
            font-weight: bold;
            transition: background-color 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #1DB954; /* Slightly darker green on hover */
            cursor: pointer;
        }

        /* Style for text input */
        .stTextInput>div>div>input {
            background-color: rgba(255, 255, 255, 0.1); /* Slightly transparent white for input background */
            color: #FFFFFF;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            padding: 10px;
        }
        .stTextInput>div>div>input:focus {
            border-color: #1ED760; /* Green border on focus */
            box-shadow: 0 0 0 0.2rem rgba(30, 215, 96, 0.25); /* Green glow on focus */
        }

        /* Style for info box */
        .stAlert {
            background-color: rgba(30, 215, 96, 0.1); /* Light green transparent background */
            color: #1ED760;
            border-left: 5px solid #1ED760;
            border-radius: 5px;
            padding: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("Spotify Music Recommender")

    # Get the access token from the URL query parameters
    query_params = st.query_params
    token = query_params.get("token")

    if token:
        st.session_state.token = token

    if "token" not in st.session_state:
        st.markdown(f"<a href=\"{BACKEND_URL}/login\" target=\"_self\" style=\"text-decoration: none;\">" +
                    "<button style=\"background-color: #1ED760; color: white; border-radius: 8px; border: none; padding: 12px 25px; font-weight: bold; cursor: pointer;\">Login with Spotify</button></a>", unsafe_allow_html=True)
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
                    result_data = query_result.get("result")
                    if isinstance(result_data, list) and all(isinstance(item, dict) for item in result_data):
                        st.dataframe(result_data)
                    else:
                        st.json(result_data)
                else:
                    st.error(f"Error: {query_result.get("message")}")
            else:
                st.warning("Please enter a query.")

if __name__ == "__main__":
    main()