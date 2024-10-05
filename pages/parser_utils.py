import os
import base64
import json
import requests
import tempfile
import logging
import streamlit as st
from urllib.parse import quote

LOCAL_PARSERS_FILE = os.path.join(tempfile.gettempdir(), 'parsers.json')
PAGES_DIRECTORY = 'pages'

# Ensure pages directory exists
if not os.path.exists(PAGES_DIRECTORY):
    os.makedirs(PAGES_DIRECTORY)

# Function to download parsers from GitHub
def download_parsers_from_github():
    headers = {'Authorization': f'token {st.secrets["github"]["access_token"]}'}
    try:
        response = requests.get(GITHUB_API_URL, headers=headers, timeout=10)
        response.raise_for_status()

        content = response.json().get('content')
        if content:
            with open(LOCAL_PARSERS_FILE, 'wb') as f:
                f.write(base64.b64decode(content))
            load_parsers()  # Load parsers after downloading
            st.success("`parsers.json` downloaded successfully from GitHub.")
        else:
            st.error("`parsers.json` content is empty.")
    except Exception as e:
        st.error(f"Error: {e}")

# Function to save parsers locally
def save_parsers():
    try:
        with open(LOCAL_PARSERS_FILE, 'w') as f:
            json.dump(st.session_state['parsers'], f, indent=4)
    except Exception as e:
        st.error(f"Error: {e}")

# Function to add a new parser
def add_new_parser():
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
                generate_parser_page(parser_name, st.session_state['parsers'][parser_name])
                st.success("The parser has been added successfully.")

# Function to generate parser page file
def generate_parser_page(parser_name, details):
    file_name = f"{parser_name.lower().replace(' ', '-')}_parser.py"
    file_path = os.path.join(PAGES_DIRECTORY, file_name)
    page_content = f"""
import streamlit as st

def main():
    st.set_page_config(page_title="{parser_name} - Parser", layout="wide")
    st.title("{parser_name} Parser")
    st.write("Parser App ID: {details['parser_app_id']}")
    st.write("Extra Accuracy: {'Yes' if details['extra_accuracy'] else 'No'}")

    # Add parser execution logic here
    st.subheader("Run Parser")
    # Implement file uploader and run parser here...

if __name__ == "__main__":
    main()
    """
    # Write the page content to the file
    with open(file_path, 'w') as f:
        f.write(page_content)

# Function to list all parsers
def list_parsers():
    st.subheader("List of All Parsers")
    if not st.session_state['parsers']:
        st.info("No parsers available. Please add a parser first.")
        return

    # Iterate over the parsers and display details
    for parser_name, details in st.session_state['parsers'].items():
        with st.expander(parser_name):
            st.write(f"**Parser App ID:** {details['parser_app_id']}")
            st.write(f"**Extra Accuracy:** {'Yes' if details['extra_accuracy'] else 'No'}")

            # Generate dynamic parser page link using URL parameters
            parser_page_link = f"https://fracto-ocr.streamlit.app/?parser={quote(parser_name)}&client=true"

            # Display link button
            st.write(f"**Parser Page Link:** [Click Here]({parser_page_link})")
            
            # Add Delete button
            if st.button(f"Delete {parser_name}", key=f"delete_{parser_name}"):
                del st.session_state['parsers'][parser_name]
                save_parsers()
                st.success(f"Parser '{parser_name}' has been deleted.")
