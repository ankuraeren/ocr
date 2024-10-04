import os
import json
import base64
import requests
import tempfile
import logging
import streamlit as st

# Define the local file path for the parsers.json
LOCAL_PARSERS_FILE = os.path.join(tempfile.gettempdir(), 'parsers.json')

# GitHub Configuration
GITHUB_REPO = 'ankuraeren/ocr'  # Your GitHub repo name
GITHUB_BRANCH = 'main'  # Define the branch
GITHUB_FILE_PATH = 'parsers.json'  # Path to the parsers.json file in GitHub
GITHUB_API_URL = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}?ref={GITHUB_BRANCH}'


def download_parsers_from_github():
    """Downloads the parsers.json file from GitHub and loads it into the session state."""
    headers = {'Authorization': f'token {st.secrets["github"]["access_token"]}'}
    try:
        response = requests.get(GITHUB_API_URL, headers=headers, timeout=10)
        response.raise_for_status()

        content = response.json().get('content')
        if content:
            with open(LOCAL_PARSERS_FILE, 'wb') as f:
                f.write(base64.b64decode(content))
            load_parsers()  # Call the function after downloading
            st.success("`parsers.json` downloaded successfully from GitHub.")
        else:
            st.error("`parsers.json` content is empty.")
    except Exception as e:
        st.error(f"Error: {e}")


def load_parsers():
    """Loads the parsers.json file from the local file to session state."""
    try:
        if os.path.exists(LOCAL_PARSERS_FILE):
            with open(LOCAL_PARSERS_FILE, 'r') as f:
                st.session_state['parsers'] = json.load(f)
        else:
            st.session_state['parsers'] = {}
    except Exception as e:
        st.error(f"Error loading parsers: {e}")


def save_parsers():
    """Saves the current parsers in session state to the local file."""
    try:
        with open(LOCAL_PARSERS_FILE, 'w') as f:
            json.dump(st.session_state['parsers'], f, indent=4)
    except Exception as e:
        st.error(f"Error: {e}")


def update_parsers_to_github():
    """Uploads the updated parsers.json to GitHub."""
    headers = {
        'Authorization': f'token {st.secrets["github"]["access_token"]}',
        'Content-Type': 'application/json'
    }
    try:
        # Get the current sha of the file (required for updating in GitHub)
        sha = get_current_sha()
        if not sha:
            return

        with open(LOCAL_PARSERS_FILE, 'rb') as f:
            content = base64.b64encode(f.read()).decode('utf-8')

        payload = {
            'message': 'Update parsers.json file',
            'content': content,
            'sha': sha,
            'branch': GITHUB_BRANCH
        }

        response = requests.put(GITHUB_API_URL, headers=headers, json=payload)

        if response.status_code in [200, 201]:
            st.success("`parsers.json` uploaded successfully to GitHub.")
        else:
            st.error(f"Failed to upload `parsers.json`: {response.text}")
    except Exception as e:
        st.error(f"Error uploading parsers: {e}")


def get_current_sha():
    """Fetches the current SHA (commit hash) of the parsers.json file in GitHub."""
    headers = {'Authorization': f'token {st.secrets["github"]["access_token"]}'}
    try:
        response = requests.get(GITHUB_API_URL, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json().get('sha')
    except Exception as e:
        st.error(f"Error fetching SHA: {e}")
        return None


def add_new_parser():
    """Adds a new parser to the session state and saves it."""
    st.subheader("Add a New Parser")
    with st.form("add_parser_form"):
        parser_name = st.text_input("Parser Name").strip()
        api_key = st.text_input("API Key").strip()
        parser_app_id = st.text_input("Parser App ID").strip()
        extra_accuracy = st.checkbox("Require Extra Accuracy")
        expected_response = st.text_area("Expected JSON Response (optional)")
        sample_curl = st.text_area("Sample CURL Request (optional)")

        submitted = st.form_submit_button("Add Parser")
        if submitted:
            if not parser_name or not api_key or not parser_app_id:
                st.error("Please fill in all required fields.")
            elif parser_name in st.session_state['parsers']:
                st.error(f"Parser '{parser_name}' already exists.")
            else:
                st.session_state['parsers'][parser_name] = {
                    'api_key': api_key,
                    'parser_app_id': parser_app_id,
                    'extra_accuracy': extra_accuracy,
                    'expected_response': expected_response,
                    'sample_curl': sample_curl
                }
                save_parsers()
                st.success("The parser has been added successfully.")


def list_parsers():
    st.subheader("List of All Parsers")
    
    # Check if parsers exist in session state
    if not st.session_state['parsers']:
        st.info("No parsers available. Please add a parser first.")
        return

    # Loop through parsers and display only the name, extra accuracy status, and delete option
    for parser_name, details in st.session_state['parsers'].items():
        with st.expander(parser_name):
            st.write(f"**Extra Accuracy:** {'Yes' if details['extra_accuracy'] else 'No'}")
            
            # Add delete button for each parser
            if st.button(f"Delete {parser_name}", key=f"delete_{parser_name}"):
                del st.session_state['parsers'][parser_name]
                save_parsers()
                st.success(f"Parser '{parser_name}' has been deleted.")
                st.experimental_rerun()  # Ensure the UI updates immediately



# Additional functionality for uploading updated parsers
def update_parsers():
    """Triggers the upload of updated parsers to GitHub."""
    if st.button("Update Parsers File"):
        save_parsers()
        update_parsers_to_github()

