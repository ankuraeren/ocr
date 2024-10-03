import pandas as pd
import streamlit as st
import requests
import os
import json
from PIL import Image
from io import BytesIO
import shutil
import tempfile
import logging
import base64
import time  # For tracking time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# GitHub Configuration
GITHUB_REPO = 'ankuraeren/ocr'
GITHUB_BRANCH = 'main'  # Define the branch
GITHUB_FILE_PATH = 'parsers.json'
GITHUB_API_URL = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}?ref={GITHUB_BRANCH}'

# Access GitHub Access Token securely from Streamlit secrets
GITHUB_ACCESS_TOKEN = st.secrets["github"]["access_token"]

# API Configuration
API_ENDPOINT = 'https://prod-ml.fracto.tech/upload-file-smart-ocr'

# Define local parsers file path using a temporary directory
LOCAL_PARSERS_FILE = os.path.join(tempfile.gettempdir(), 'parsers.json')

# Initialize parsers dictionary in session state
if 'parsers' not in st.session_state:
    st.session_state['parsers'] = {}

def download_parsers_from_github():
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

def get_current_sha():
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

def upload_parsers_to_github():
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

def load_parsers():
    if os.path.exists(LOCAL_PARSERS_FILE):
        try:
            with open(LOCAL_PARSERS_FILE, 'r') as f:
                st.session_state['parsers'] = json.load(f)
            logging.info("Parsers loaded successfully.")
            st.success("parsers.json loaded successfully.")
        except json.JSONDecodeError:
            logging.error("parsers.json is not a valid JSON file.")
            st.error("parsers.json is corrupted or not in valid JSON format.")
        except Exception as e:
            logging.error(f"Unexpected error while loading parsers.json: {e}")
            st.error(f"Unexpected error while loading parsers.json: {e}")
    else:
        st.session_state['parsers'] = {}
        logging.info("parsers.json not found. Starting with an empty parsers dictionary.")
        st.info("parsers.json not found. Starting with an empty parsers dictionary.")

def save_parsers():
    try:
        with open(LOCAL_PARSERS_FILE, 'w') as f:
            json.dump(st.session_state['parsers'], f, indent=4)
        st.success("parsers.json has been updated locally. Please upload it back to GitHub.")
        logging.info("parsers.json has been updated locally.")
    except Exception as e:
        st.error(f"Failed to save parsers.json locally: {e}")
        logging.error(f"Failed to save parsers.json locally: {e}")

def add_new_parser():
    st.subheader("Add a New Parser")
    with st.form("add_parser_form"):
        parser_name = st.text_input("Parser Name (e.g., 'Cheque Front')").strip()
        api_key = st.text_input("API Key").strip()
        parser_app_id = st.text_input("Parser App ID").strip()
        extra_accuracy = st.checkbox("Require Extra Accuracy")
        expected_response = st.text_area("Expected JSON Response (optional)")
        sample_curl = st.text_area("Sample CURL Request (optional)")
        
        submitted = st.form_submit_button("Add Parser")
        if submitted:
            if not parser_name or not api_key or not parser_app_id:
                st.error("Please fill in all required fields (Parser Name, API Key, Parser App ID).")
            elif parser_name in st.session_state['parsers']:
                st.error(f"Parser '{parser_name}' already exists.")
            else:
                if expected_response:
                    try:
                        json.loads(expected_response)
                    except json.JSONDecodeError:
                        st.error("Expected JSON Response is not a valid JSON.")
                        return
                
                st.session_state['parsers'][parser_name] = {
                    'api_key': api_key,
                    'parser_app_id': parser_app_id,
                    'extra_accuracy': extra_accuracy,
                    'expected_response': expected_response,
                    'sample_curl': sample_curl
                }
                save_parsers()

def list_parsers():
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
            
            delete_button = st.button(f"Delete {parser_name}", key=f"delete_{parser_name}")
            if delete_button:
                del st.session_state['parsers'][parser_name]
                save_parsers()
                st.success(f"Parser '{parser_name}' has been deleted.")
                st.experimental_rerun()

def run_parser(parsers):
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
        uploaded_files = st.file_uploader("Choose image(s)...", type=["jpg", "jpeg", "png", "bmp", "gif", "tiff"], accept_multiple_files=True)
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

    if parser_info['extra_accuracy']:
        extra_accuracy = st.checkbox("Enable Extra Accuracy", value=True)
    else:
        extra_accuracy = False

    if st.button("Run OCR"):
        if not image_paths and not images:
            st.error("Please provide at least one image to process.")
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
        if extra_accuracy:
            form_data['extra_accuracy'] = 'true'

        files = []
        if image_paths:
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
                    return

        try:
            start_time = time.time()  # Track start time
            with st.spinner("Processing OCR..."):  # Loading indicator
                logging.info(f"Sending POST request to {API_ENDPOINT} with Parser App ID: {form_data['parserApp']}")
                response = requests.post(API_ENDPOINT, headers=headers, data=form_data, files=files if files else None, timeout=120)
                logging.info(f"Received response with status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error making API request: {e}")
            st.error(f"Error making API request: {e}")
            return
        finally:
            for _, file_tuple in files:
                file_tuple[1].close()

        time_taken = time.time() - start_time  # Calculate time taken
        st.success(f"OCR Parsing Successful! Time Taken: {time_taken:.2f} seconds")

        if response.status_code == 200:
            try:
                response_json = response.json()
                formatted_json = json.dumps(response_json, indent=4)
                st.json(response_json)

                parsed_data = response_json.get('parsedData', {})

                st.markdown("---")

                st.subheader("Processed Images")
                if images:
                    num_images = len(images)
                    cols = st.columns(min(num_images, 5))
                    for idx, img in enumerate(images):
                        cols[idx % 5].image(img, caption=f"Image {idx+1}", use_column_width=True)

                st.markdown("---")

                st.subheader("Summary Table")
                if parsed_data:
                    if isinstance(parsed_data, dict) and all(not isinstance(v, (dict, list)) for v in parsed_data.values()):
                        line_items = [(key, value) for key, value in parsed_data.items()]
                        df = pd.DataFrame(line_items, columns=["Field", "Value"])
                    elif isinstance(parsed_data, dict):
                        line_items = []
                        for section, fields in parsed_data.items():
                            if isinstance(fields, dict):
                                for key, value in fields.items():
                                    line_items.append((f"{section} - {key}", value))
                            elif isinstance(fields, list):
                                for item in fields:
                                    if isinstance(item, dict):
                                        for key, value in item.items():
                                            line_items.append((f"{section} - {key}", value))
                        df = pd.DataFrame(line_items, columns=["Field", "Value"])
                    elif isinstance(parsed_data, list):
                        df = pd.DataFrame(parsed_data)
                    else:
                        df = pd.DataFrame()

                    if not df.empty:
                        st.dataframe(
                            df.style.applymap(lambda val: 'background-color: #f7f9fc' if pd.isna(val) else 'background-color: #e3f2fd'), 
                            width=st.sidebar.slider("Adjust table width", 800, 1200, 1000),
                            height=400  # Fixed height
                        )
                    else:
                        st.info("Parsed data format is not supported for table display.")
                else:
                    st.info("No parsed data available to display in table format.")

            except json.JSONDecodeError:
                logging.error("Failed to parse JSON response.")
                st.error("Failed to parse JSON response.")
                st.text(response.text)
        else:
            logging.error(f"Request failed with status code {response.status_code}")
            try:
                error_response = response.json()
                st.error(f"Request failed with status code {response.status_code}")
                st.json(error_response)
            except json.JSONDecodeError:
                st.error(f"Request failed with status code {response.status_code}")
                st.text(response.text)

        for temp_dir in temp_dirs:
            try:
                shutil.rmtree(temp_dir)
                logging.info(f"Cleaned up temporary directory {temp_dir}")
            except Exception as e:
                logging.warning(f"Could not remove temporary directory {temp_dir}: {e}")

def main():
    st.set_page_config(page_title="FRACTO OCR Parser", layout="wide")

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

    # Ensure parsers.json is downloaded and loaded at the start
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
