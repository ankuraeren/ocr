import logging
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import base64  # Add this line to import the base64 module
import base64

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# GitHub Configuration
# GitHub Configuration using Streamlit Secrets
GITHUB_REPO = 'ankuraeren/ocr'
GITHUB_FILE_PATH = 'parsers.json'
GITHUB_API_URL = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}'
GITHUB_ACCESS_TOKEN = st.secrets["github"]["access_token"]

# Define local parsers file path
LOCAL_PARSERS_FILE = 'parsers.json'
# Access GitHub Access Token securely from secrets
GITHUB_ACCESS_TOKEN = st.secrets["github"]["access_token"]

# Access API Endpoint securely from secrets
API_ENDPOINT = st.secrets["api"]["endpoint"]

# Define local parsers file path using a temporary directory
LOCAL_PARSERS_FILE = os.path.join(tempfile.gettempdir(), 'parsers.json')

# Initialize parsers dictionary in session state
    if 'parsers' not in st.session_state:
        @@ -32,18 +37,35 @@

def download_parsers_from_github():
headers = {'Authorization': f'token {GITHUB_ACCESS_TOKEN}'}
    response = requests.get(GITHUB_API_URL, headers=headers)
    try:
        response = requests.get(GITHUB_API_URL, headers=headers, timeout=10)
        response.raise_for_status()  # Raises HTTPError for bad responses

    if response.status_code == 200:
content = response.json().get('content')
        with open(LOCAL_PARSERS_FILE, 'wb') as f:
            f.write(base64.b64decode(content))
        load_parsers()
        st.success("parsers.json downloaded successfully from GitHub.")
        logging.info("parsers.json downloaded successfully from GitHub.")
    else:
        st.error("Failed to download parsers.json from GitHub.")
        logging.error(f"Failed to download parsers.json from GitHub. Status Code: {response.status_code}")
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
try:
@@ -54,7 +76,10 @@ def upload_parsers_to_github():
if not current_sha:
return

        headers = {'Authorization': f'token {GITHUB_ACCESS_TOKEN}', 'Content-Type': 'application/json'}
        headers = {
            'Authorization': f'token {GITHUB_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
payload = {
'message': 'Update parsers.json file',
'content': content,
@@ -63,37 +88,75 @@ def upload_parsers_to_github():
}

response = requests.put(GITHUB_API_URL, headers=headers, json=payload)
        

if response.status_code in [200, 201]:
            st.success("parsers.json uploaded successfully to GitHub.")
            st.success("`parsers.json` uploaded successfully to GitHub.")
            logging.info("`parsers.json` uploaded successfully to GitHub.")
else:
error_message = response.json().get('message', 'Unknown error')
            st.error(f"Failed to upload parsers.json to GitHub: {error_message}")
            st.error(f"Failed to upload `parsers.json` to GitHub: {error_message}")
            logging.error(f"Failed to upload `parsers.json` to GitHub: {error_message}")
    except FileNotFoundError:
        st.error("`parsers.json` file not found locally. Please download it first.")
        logging.error("`parsers.json` file not found locally.")
except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        st.error(f"An unexpected error occurred during upload: {e}")
        logging.error(f"An unexpected error occurred during upload: {e}")

def get_current_sha():
headers = {'Authorization': f'token {GITHUB_ACCESS_TOKEN}'}
    response = requests.get(GITHUB_API_URL, headers=headers)

    if response.status_code == 200:
        return response.json().get('sha')
    else:
        st.error("Failed to get current file SHA from GitHub.")
        return None
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
if os.path.exists(LOCAL_PARSERS_FILE):
        with open(LOCAL_PARSERS_FILE, 'r') as f:
            try:
        try:
            with open(LOCAL_PARSERS_FILE, 'r') as f:
st.session_state['parsers'] = json.load(f)
            except json.JSONDecodeError:
                st.error("parsers.json is corrupted or not in valid JSON format.")
            logging.info("`parsers.json` loaded into session state.")
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
    with open(LOCAL_PARSERS_FILE, 'w') as f:
        json.dump(st.session_state['parsers'], f, indent=4)
    st.success("parsers.json has been updated locally. Please upload it back to GitHub.")
    try:
        with open(LOCAL_PARSERS_FILE, 'w') as f:
            json.dump(st.session_state['parsers'], f, indent=4)
        st.success("`parsers.json` has been updated locally. Please upload it back to GitHub.")
        logging.info("`parsers.json` has been updated locally.")
    except Exception as e:
        st.error(f"Failed to save `parsers.json` locally: {e}")
        logging.error(f"Failed to save `parsers.json` locally: {e}")

def add_new_parser():
st.subheader("Add a New Parser")
@@ -127,7 +190,7 @@ def add_new_parser():
'sample_curl': sample_curl
}
save_parsers()
                st.info("The parser has been added successfully.")
                st.success("The parser has been added successfully.")
st.experimental_set_query_params(refresh='true')

def list_parsers():
@@ -186,14 +249,18 @@ def run_parser(parsers):
uploaded_files = st.file_uploader("Choose image(s)...", type=["jpg", "jpeg", "png", "bmp", "gif", "tiff"], accept_multiple_files=True)
if uploaded_files:
for uploaded_file in uploaded_files:
                image = Image.open(uploaded_file)
                images.append(image)
                st.image(image, caption=uploaded_file.name, use_column_width=True)
                temp_dir = tempfile.mkdtemp()
                temp_dirs.append(temp_dir)
                image_path = os.path.join(temp_dir, uploaded_file.name)
                image.save(image_path)
                image_paths.append(image_path)
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
@@ -204,18 +271,21 @@ def run_parser(parsers):
if response.status_code == 200:
image = Image.open(BytesIO(response.content))
images.append(image)
                        st.image(image, caption=os.path.basename(url.split('?')[0]), use_column_width=True)
                        image_caption = os.path.basename(url.split('?')[0]) or "Image"
                        st.image(image, caption=image_caption, use_column_width=True)
temp_dir = tempfile.mkdtemp()
temp_dirs.append(temp_dir)
                        image_filename = os.path.basename(url.split('?')[0])
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
@@ -252,10 +322,14 @@ def send_request(extra_accuracy):
'.tiff': 'image/tiff'
}
mime_type = mime_types.get(file_ext, 'application/octet-stream')
                files.append(('file', (os.path.basename(image_path), open(image_path, 'rb'), mime_type)))
                try:
                    files.append(('file', (os.path.basename(image_path), open(image_path, 'rb'), mime_type)))
                except Exception as e:
                    st.error(f"Error opening file {image_path}: {e}")
                    logging.error(f"Error opening file {image_path}: {e}")
                    return None

try:
                # Simulate sending request
logging.info(f"Sending POST request to {API_ENDPOINT} with Parser App ID: {local_form_data['parserApp']}, Extra Accuracy: {extra_accuracy}")
response = requests.post(API_ENDPOINT, headers=local_headers, data=local_form_data, files=files if files else None, timeout=120)
logging.info(f"Received response: {response.status_code}")
@@ -273,27 +347,51 @@ def send_request(extra_accuracy):
response_extra = send_request(True)
response_no_extra = send_request(False)

        # Cleanup temporary directories
for temp_dir in temp_dirs:
try:
shutil.rmtree(temp_dir)
except Exception as e:
logging.error(f"Error removing temp dir {temp_dir}: {e}")

        if response_extra and response_no_extra and response_extra.status_code == 200 and response_no_extra.status_code == 200:
            try:
                response_json_extra = response_extra.json()
                response_json_no_extra = response_no_extra.json()

                col1, col2 = st.columns(2)
                with col1:
                    st.expander(f"Results with Extra Accuracy").json(response_json_extra)
                with col2:
                    st.expander(f"Results without Extra Accuracy").json(response_json_no_extra)

            except json.JSONDecodeError:
                st.error("Failed to parse JSON response.")
        else: 
            st.error("Both requests failed. Please try again.")
        if response_extra and response_no_extra:
            success_extra = response_extra.status_code == 200
            success_no_extra = response_no_extra.status_code == 200

            if success_extra:
                try:
                    response_json_extra = response_extra.json()
                    col1, col2 = st.columns(2)
                    with col1:
                        with st.expander("Results with Extra Accuracy"):
                            st.json(response_json_extra)
                except json.JSONDecodeError:
                    st.error("Failed to parse JSON response with Extra Accuracy.")
                    logging.error("Failed to parse JSON response with Extra Accuracy.")

            else:
                st.error("Request with Extra Accuracy failed.")
                logging.error(f"Request with Extra Accuracy failed with status code: {response_extra.status_code}")

            if success_no_extra:
                try:
                    response_json_no_extra = response_no_extra.json()
                    with st.container():
                        with st.expander("Results without Extra Accuracy"):
                            st.json(response_json_no_extra)
                except json.JSONDecodeError:
                    st.error("Failed to parse JSON response without Extra Accuracy.")
                    logging.error("Failed to parse JSON response without Extra Accuracy.")
            else:
                st.error("Request without Extra Accuracy failed.")
                logging.error(f"Request without Extra Accuracy failed with status code: {response_no_extra.status_code}")

            if success_extra and success_no_extra:
                st.success("Both OCR requests completed successfully.")
            else:
                st.error("One or both OCR requests failed. Please check the logs for more details.")
        else:
            st.error("One or both OCR requests did not receive a response.")

def main():
st.set_page_config(page_title="FRACTO OCR Parser", layout="wide")
