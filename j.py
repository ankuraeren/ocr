import os
import json
import requests
import streamlit as st
from PIL import Image
from io import BytesIO
import tempfile
import shutil
import logging
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import base64

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# GitHub Configuration using Streamlit Secrets
GITHUB_REPO = 'ankuraeren/ocr'
GITHUB_BRANCH = 'main'  # Define the branch
GITHUB_FILE_PATH = 'parsers.json'
GITHUB_API_URL = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}?ref={GITHUB_BRANCH}'

# Access GitHub Access Token securely from secrets
GITHUB_ACCESS_TOKEN = st.secrets["github"]["access_token"]

# Access API Endpoint securely from secrets
API_ENDPOINT = st.secrets["api"]["endpoint"]

# Define local parsers file path using a temporary directory
LOCAL_PARSERS_FILE = os.path.join(tempfile.gettempdir(), 'parsers.json')

# Initialize parsers dictionary in session state
if 'parsers' not in st.session_state:
    st.session_state['parsers'] = {}

if 'refresh' not in st.session_state:
    st.session_state['refresh'] = False

def download_parsers_from_github():
    """
    Download parsers.json from GitHub and load it into session state.
    """
    headers = {'Authorization': f'token {GITHUB_ACCESS_TOKEN}'}
    try:
        response = requests.get(GITHUB_API_URL, headers=headers, timeout=10)
        response.raise_for_status()  # Raises HTTPError for bad responses

        content = response.json().get('content')
        if content:
            with open(LOCAL_PARSERS_FILE, 'wb') as f:
                f.write(base64.b64decode(content))
            load_parsers()
            st.success("`parsers.json` downloaded successfully from GitHub.")
            logging.info("`parsers.json` downloaded successfully from GitHub.")
        else:
            st.error("`parsers.json` content is empty.")
            logging.error("`parsers.json` content is empty.")
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred while downloading `parsers.json`: {http_err}")
        logging.error(f"HTTP error occurred while downloading `parsers.json`: {http_err}")
    except requests.exceptions.ConnectionError as conn_err:
        st.error(f"Connection error occurred while downloading `parsers.json`: {conn_err}")
        logging.error(f"Connection error occurred while downloading `parsers.json`: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        st.error(f"Timeout error occurred while downloading `parsers.json`: {timeout_err}")
        logging.error(f"Timeout error occurred while downloading `parsers.json`: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        st.error(f"An error occurred while downloading `parsers.json`: {req_err}")
        logging.error(f"An error occurred while downloading `parsers.json`: {req_err}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        logging.error(f"Unexpected error: {e}")

def upload_parsers_to_github():
    """
    Upload the updated parsers.json to GitHub.
    """
    try:
        if not os.path.exists(LOCAL_PARSERS_FILE):
            st.error("`parsers.json` file not found locally. Please download it first.")
            logging.error("`parsers.json` file not found locally.")
            return

        with open(LOCAL_PARSERS_FILE, 'rb') as f:
            content = base64.b64encode(f.read()).decode('utf-8')

        current_sha = get_current_sha()
        if not current_sha:
            return

        headers = {
            'Authorization': f'token {GITHUB_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        payload = {
            'message': 'Update parsers.json file',
            'content': content,
            'sha': current_sha,
            'branch': GITHUB_BRANCH
        }

        response = requests.put(GITHUB_API_URL, headers=headers, json=payload)

        if response.status_code in [200, 201]:
            st.success("`parsers.json` uploaded successfully to GitHub.")
            logging.info("`parsers.json` uploaded successfully to GitHub.")
        else:
            error_message = response.json().get('message', 'Unknown error')
            st.error(f"Failed to upload `parsers.json` to GitHub: {error_message}")
            logging.error(f"Failed to upload `parsers.json` to GitHub: {error_message}")
    except FileNotFoundError:
        st.error("`parsers.json` file not found locally. Please download it first.")
        logging.error("`parsers.json` file not found locally.")
    except Exception as e:
        st.error(f"An unexpected error occurred during upload: {e}")
        logging.error(f"An unexpected error occurred during upload: {e}")

def get_current_sha():
    """
    Retrieve the current SHA of parsers.json from GitHub.
    """
    headers = {'Authorization': f'token {GITHUB_ACCESS_TOKEN}'}
    try:
        response = requests.get(GITHUB_API_URL, headers=headers, timeout=10)
        response.raise_for_status()
        sha = response.json().get('sha')
        if sha:
            return sha
        else:
            st.error("SHA not found for `parsers.json` in GitHub.")
            logging.error("SHA not found for `parsers.json` in GitHub.")
            return None
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred while fetching SHA: {http_err}")
        logging.error(f"HTTP error occurred while fetching SHA: {http_err}")
    except requests.exceptions.ConnectionError as conn_err:
        st.error(f"Connection error occurred while fetching SHA: {conn_err}")
        logging.error(f"Connection error occurred while fetching SHA: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        st.error(f"Timeout error occurred while fetching SHA: {timeout_err}")
        logging.error(f"Timeout error occurred while fetching SHA: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        st.error(f"An error occurred while fetching SHA: {req_err}")
        logging.error(f"An error occurred while fetching SHA: {req_err}")
    except Exception as e:
        st.error(f"Unexpected error while fetching SHA: {e}")
        logging.error(f"Unexpected error while fetching SHA: {e}")
    return None

def load_parsers():
    """
    Load parsers from the local parsers.json file into session state.
    """
    if os.path.exists(LOCAL_PARSERS_FILE):
        try:
            with open(LOCAL_PARSERS_FILE, 'r') as f:
                parsers = json.load(f)
                st.session_state['parsers'] = parsers
            logging.info("`parsers.json` loaded into session state.")
            st.success("`parsers.json` loaded successfully.")
            logging.debug(f"Loaded parsers: {parsers}")  # Detailed log
        except json.JSONDecodeError:
            st.error("`parsers.json` is corrupted or not in valid JSON format.")
            logging.error("`parsers.json` is corrupted or not in valid JSON format.")
        except Exception as e:
            st.error(f"Unexpected error while loading `parsers.json`: {e}")
            logging.error(f"Unexpected error while loading `parsers.json`: {e}")
    else:
        st.error("`parsers.json` does not exist locally. Please download it from GitHub.")
        logging.error("`parsers.json` does not exist locally.")

def save_parsers():
    """
    Save the parsers from session state to the local parsers.json file.
    """
    try:
        with open(LOCAL_PARSERS_FILE, 'w') as f:
            json.dump(st.session_state['parsers'], f, indent=4)
        st.success("`parsers.json` has been updated locally. Please upload it back to GitHub.")
        logging.info("`parsers.json` has been updated locally.")
    except Exception as e:
        st.error(f"Failed to save `parsers.json` locally: {e}")
        logging.error(f"Failed to save `parsers.json` locally: {e}")

def add_new_parser():
    """
    Form to add a new OCR parser.
    """
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
                if expected_response:
                    try:
                        json.loads(expected_response)
                    except json.JSONDecodeError:
                        st.error("Expected JSON Response is not valid JSON.")
                        return

                st.session_state['parsers'][parser_name] = {
                    'api_key': api_key,
                    'parser_app_id': parser_app_id,
                    'extra_accuracy': extra_accuracy,
                    'expected_response': expected_response,
                    'sample_curl': sample_curl
                }
                save_parsers()
                st.success("The parser has been added successfully.")
                st.experimental_set_query_params(refresh='true')

def list_parsers():
    """
    List all existing OCR parsers.
    """
    st.subheader("List of All Parsers")
    if not st.session_state['parsers']:
        st.info("No parsers available. Please add a parser first.")
        return

    for parser_name, details in st.session_state['parsers'].items():
        with st.expander(parser_name):
            st.write(f"**API Key:** {details['api_key']}")
            st.write(f"**Parser App ID:** {details['parser_app_id']}")
            st.write(f"**Extra Accuracy:** {'Yes' if details['extra_accuracy'] else 'No'}")
            st.write(f"**Expected Response:**")
            if details['expected_response']:
                try:
                    expected_json = json.loads(details['expected_response'])
                    st.json(expected_json)
                except json.JSONDecodeError:
                    st.text(details['expected_response'])
            else:
                st.write("N/A")
            st.write(f"**Sample CURL Request:**")
            if details['sample_curl']:
                st.code(details['sample_curl'], language='bash')
            else:
                st.write("N/A")
            
            if st.button(f"Delete {parser_name}", key=f"delete_{parser_name}"):
                del st.session_state['parsers'][parser_name]
                save_parsers()
                st.success(f"Parser '{parser_name}' has been deleted.")
                st.experimental_set_query_params(refresh='true')

def run_parser(parsers):
    """
    Run the OCR parser by sending requests to the OCR API and displaying the results.
    """
    st.subheader("Run OCR Parser")
    if not parsers:
        st.info("No parsers available. Please add a parser first.")
        return

    parser_names = list(parsers.keys())
    selected_parser = st.selectbox("Select Parser", parser_names)
    parser_info = parsers[selected_parser]

    st.write(f"**Selected Parser:** {selected_parser}")
    st.write(f"**Parser App ID:** {parser_info['parser_app_id']}")
    st.write(f"**Extra Accuracy Required:** {'Yes' if parser_info['extra_accuracy'] else 'No'}")

    input_method = st.radio("Choose Input Method", ("Upload Image File", "Enter Image URL"))

    image_paths = []
    images = []
    temp_dirs = []

    if input_method == "Upload Image File":
        uploaded_files = st.file_uploader(
            "Choose image(s)...",
            type=["jpg", "jpeg", "png", "bmp", "gif", "tiff"],
            accept_multiple_files=True
        )
        if uploaded_files:
            for uploaded_file in uploaded_files:
                try:
                    image = Image.open(uploaded_file)
                    images.append(image)
                    st.image(image, caption=uploaded_file.name, use_column_width=True)
                    temp_dir = tempfile.mkdtemp()
                    temp_dirs.append(temp_dir)
                    image_path = os.path.join(temp_dir, uploaded_file.name)
                    image.save(image_path)
                    image_paths.append(image_path)
                except Exception as e:
                    st.error(f"Error processing file {uploaded_file.name}: {e}")
                    logging.error(f"Error processing file {uploaded_file.name}: {e}")
    else:
        image_urls = st.text_area("Enter Image URLs (one per line)")
        if image_urls:
            urls = image_urls.strip().split('\n')
            for url in urls:
                try:
                    response = requests.get(url.strip(), stream=True, timeout=30)
                    if response.status_code == 200:
                        image = Image.open(BytesIO(response.content))
                        images.append(image)
                        image_caption = os.path.basename(url.split('?')[0]) or "Image"
                        st.image(image, caption=image_caption, use_column_width=True)
                        temp_dir = tempfile.mkdtemp()
                        temp_dirs.append(temp_dir)
                        image_filename = os.path.basename(url.split('?')[0]) or "image.jpg"
                        image_path = os.path.join(temp_dir, image_filename)
                        with open(image_path, 'wb') as f:
                            shutil.copyfileobj(response.raw, f)
                        image_paths.append(image_path)
                    else:
                        st.error(f"Failed to download image from {url}. Status Code: {response.status_code}")
                        logging.error(f"Failed to download image from {url}. Status Code: {response.status_code}")
                except Exception as e:
                    st.error(f"Error downloading image from {url}: {e}")
                    logging.error(f"Error downloading image from {url}: {e}")

    if st.button("Run OCR"):
        if not image_paths and not images:
            st.error("Please provide at least one image.")
            return

        headers = {
            'x-api-key': parser_info['api_key'],
        }

        form_data = {
            'parserApp': parser_info['parser_app_id'],
            'user_ip': '127.0.0.1',
            'location': 'delhi',
            'user_agent': 'Dummy-device-testing11',
        }

        def send_request(extra_accuracy):
            """
            Send a POST request to the OCR API with the specified extra_accuracy flag.
            """
            local_headers = headers.copy()
            local_form_data = form_data.copy()
            if extra_accuracy:
                local_form_data['extra_accuracy'] = 'true'

            # List of files to upload
            files = []
            for image_path in image_paths:
                _, file_ext = os.path.splitext(image_path.lower())
                mime_types = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.bmp': 'image/bmp',
                    '.gif': 'image/gif',
                    '.tiff': 'image/tiff'
                }
                mime_type = mime_types.get(file_ext, 'application/octet-stream')
                try:
                    files.append(('file', (os.path.basename(image_path), open(image_path, 'rb'), mime_type)))
                except Exception as e:
                    st.error(f"Error opening file {image_path}: {e}")
                    logging.error(f"Error opening file {image_path}: {e}")
                    return None

            try:
                logging.info(f"Sending POST request to {API_ENDPOINT} with Parser App ID: {local_form_data['parserApp']}, Extra Accuracy: {extra_accuracy}")
                response = requests.post(
                    API_ENDPOINT,
                    headers=local_headers,
                    data=local_form_data,
                    files=files if files else None,
                    timeout=120
                )
                logging.info(f"Received response: {response.status_code} - {response.text}")  # Log status code and response
                return response
            except requests.exceptions.RequestException as e:
                logging.error(f"Error in API request: {e}")
                st.error(f"Error in API request: {e}")
                return None
            finally:
                # Cleanup files
                for _, file_tuple in files:
                    file_tuple[1].close()

        with st.spinner("Processing OCR..."):
            # Send two separate API requests
            response_extra = send_request(True)
            response_no_extra = send_request(False)

        # Cleanup temporary directories
        for temp_dir in temp_dirs:
            try:
                shutil.rmtree(temp_dir)
                logging.info(f"Cleaned up temporary directory {temp_dir}")
            except Exception as e:
                logging.warning(f"Could not remove temporary directory {temp_dir}: {e}")

        # Display Responses
        if response_extra and response_no_extra:
            success_extra = response_extra.status_code == 200
            success_no_extra = response_no_extra.status_code == 200

            cols = st.columns(2)  # Create two columns for side-by-side display

            # Display Results with Extra Accuracy
            if success_extra:
                try:
                    response_json_extra = response_extra.json()
                    with cols[0]:
                        with st.expander("Results with Extra Accuracy"):
                            st.json(response_json_extra)
                except json.JSONDecodeError:
                    st.error("Failed to parse JSON response with Extra Accuracy.")
                    logging.error("Failed to parse JSON response with Extra Accuracy.")
                    st.text(response_extra.text)
            else:
                with cols[0]:
                    st.error(f"Request with Extra Accuracy failed with status code: {response_extra.status_code}")
                    try:
                        error_response = response_extra.json()
                        st.json(error_response)
                    except json.JSONDecodeError:
                        st.text(response_extra.text)

            # Display Results without Extra Accuracy
            if success_no_extra:
                try:
                    response_json_no_extra = response_no_extra.json()
                    with cols[1]:
                        with st.expander("Results without Extra Accuracy"):
                            st.json(response_json_no_extra)
                except json.JSONDecodeError:
                    st.error("Failed to parse JSON response without Extra Accuracy.")
                    logging.error("Failed to parse JSON response without Extra Accuracy.")
                    st.text(response_no_extra.text)
            else:
                with cols[1]:
                    st.error(f"Request without Extra Accuracy failed with status code: {response_no_extra.status_code}")
                    try:
                        error_response = response_no_extra.json()
                        st.json(error_response)
                    except json.JSONDecodeError:
                        st.text(response_no_extra.text)

            # Summary Message
            if success_extra and success_no_extra:
                st.success("Both OCR requests completed successfully.")
            else:
                st.error("One or both OCR requests failed. Please check the logs for more details.")
        else:
            st.error("One or both OCR requests did not receive a response.")

def main():
    """
    Main function to run the Streamlit app.
    """
    st.set_page_config(page_title="FRACTO OCR Parser", layout="wide")

    # Custom CSS for styling
    st.markdown("""
        <style>
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 10px 24px;
            font-size: 16px;
            cursor: pointer;
            border-radius: 8px;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .sidebar .sidebar-content {
            background-color: #f8f9fa;
            padding-top: 20px;
            height: 100%;
        }
        .sidebar .sidebar-content h2 {
            color: #333;
        }
        .sidebar .sidebar-content p {
            color: #555;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("📄 FRACTO OCR Parser Web App")
    st.sidebar.header("Navigation")
    st.sidebar.markdown("""
        <p>This app provides functionalities for:</p>
        <ul>
            <li>Add OCR parsers</li>
            <li>List existing parsers</li>
            <li>Run parsers on images</li>
        </ul>
    """, unsafe_allow_html=True)

    menu = ["List Parsers", "Run Parser", "Add Parser"]
    choice = st.sidebar.radio("Menu", menu)

    # Ensure parsers are loaded only once
    if 'loaded' not in st.session_state:
        download_parsers_from_github()
        st.session_state.loaded = True

    if choice == "Add Parser":
        add_new_parser()
    elif choice == "List Parsers":
        list_parsers()
    elif choice == "Run Parser":
        run_parser(st.session_state['parsers'])

    st.sidebar.header("GitHub Actions")
    if st.sidebar.button("Download Parsers"):
        download_parsers_from_github()

    if st.sidebar.button("Update Parsers File"):
        upload_parsers_to_github()

if __name__ == "__main__":
    main()
