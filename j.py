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
import time
from pdf2image import convert_from_path
import uuid

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
# Initialize parsers dictionary and OCR results in session state
if 'parsers' not in st.session_state:
    st.session_state['parsers'] = {}

# Initialize OCR results in session state
if 'ocr_results' not in st.session_state:
    st.session_state['ocr_results'] = {
        'response_extra': None,
        'time_taken_extra': None,
        'response_no_extra': None,
        'time_taken_no_extra': None,
        'comparison_results': None,
        'comparison_table': None,
        'pdf_pages': []  # To store PDF pages as images
    }

# Initialize selected parser and active menu
if 'selected_parser' not in st.session_state:
    st.session_state['selected_parser'] = None

if 'active_menu' not in st.session_state:
    st.session_state['active_menu'] = "List Parsers"

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
            st.sidebar.success("`parsers.json` downloaded successfully from GitHub.")
logging.info("`parsers.json` downloaded successfully from GitHub.")
else:
            st.error("`parsers.json` content is empty.")
            st.sidebar.error("`parsers.json` content is empty.")
logging.error("`parsers.json` content is empty.")
except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred while downloading `parsers.json`: {http_err}")
        st.sidebar.error(f"HTTP error occurred while downloading `parsers.json`: {http_err}")
logging.error(f"HTTP error occurred while downloading `parsers.json`: {http_err}")
except requests.exceptions.ConnectionError as conn_err:
        st.error(f"Connection error occurred while downloading `parsers.json`: {conn_err}")
        st.sidebar.error(f"Connection error occurred while downloading `parsers.json`: {conn_err}")
logging.error(f"Connection error occurred while downloading `parsers.json`: {conn_err}")
except requests.exceptions.Timeout as timeout_err:
        st.error(f"Timeout error occurred while downloading `parsers.json`: {timeout_err}")
        st.sidebar.error(f"Timeout error occurred while downloading `parsers.json`: {timeout_err}")
logging.error(f"Timeout error occurred while downloading `parsers.json`: {timeout_err}")
except requests.exceptions.RequestException as req_err:
        st.error(f"An error occurred while downloading `parsers.json`: {req_err}")
        st.sidebar.error(f"An error occurred while downloading `parsers.json`: {req_err}")
logging.error(f"An error occurred while downloading `parsers.json`: {req_err}")
except Exception as e:
        st.error(f"Unexpected error: {e}")
        st.sidebar.error(f"Unexpected error: {e}")
logging.error(f"Unexpected error: {e}")

def upload_parsers_to_github():
try:
if not os.path.exists(LOCAL_PARSERS_FILE):
            st.error("`parsers.json` file not found locally. Please download it first.")
            st.sidebar.error("`parsers.json` file not found locally. Please download it first.")
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
'branch': GITHUB_BRANCH  # Corrected: Removed duplicate 'branch' key
}

response = requests.put(GITHUB_API_URL, headers=headers, json=payload)

if response.status_code in [200, 201]:
            st.success("`parsers.json` uploaded successfully to GitHub.")
            st.sidebar.success("`parsers.json` uploaded successfully to GitHub.")
logging.info("`parsers.json` uploaded successfully to GitHub.")
else:
error_message = response.json().get('message', 'Unknown error')
            st.error(f"Failed to upload `parsers.json` to GitHub: {error_message}")
            st.sidebar.error(f"Failed to upload `parsers.json` to GitHub: {error_message}")
logging.error(f"Failed to upload `parsers.json` to GitHub: {error_message}")
except FileNotFoundError:
        st.error("`parsers.json` file not found locally. Please download it first.")
        st.sidebar.error("`parsers.json` file not found locally. Please download it first.")
logging.error("`parsers.json` file not found locally.")
except Exception as e:
        st.error(f"An unexpected error occurred during upload: {e}")
        st.sidebar.error(f"An unexpected error occurred during upload: {e}")
logging.error(f"An unexpected error occurred during upload: {e}")

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
            st.sidebar.error("SHA not found for `parsers.json` in GitHub.")
logging.error("SHA not found for `parsers.json` in GitHub.")
return None
except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred while fetching SHA: {http_err}")
        st.sidebar.error(f"HTTP error occurred while fetching SHA: {http_err}")
logging.error(f"HTTP error occurred while fetching SHA: {http_err}")
except requests.exceptions.ConnectionError as conn_err:
        st.error(f"Connection error occurred while fetching SHA: {conn_err}")
        st.sidebar.error(f"Connection error occurred while fetching SHA: {conn_err}")
logging.error(f"Connection error occurred while fetching SHA: {conn_err}")
except requests.exceptions.Timeout as timeout_err:
        st.error(f"Timeout error occurred while fetching SHA: {timeout_err}")
        st.sidebar.error(f"Timeout error occurred while fetching SHA: {timeout_err}")
logging.error(f"Timeout error occurred while fetching SHA: {timeout_err}")
except requests.exceptions.RequestException as req_err:
        st.error(f"An error occurred while fetching SHA: {req_err}")
        st.sidebar.error(f"An error occurred while fetching SHA: {req_err}")
logging.error(f"An error occurred while fetching SHA: {req_err}")
except Exception as e:
        st.error(f"Unexpected error while fetching SHA: {e}")
        st.sidebar.error(f"Unexpected error while fetching SHA: {e}")
logging.error(f"Unexpected error while fetching SHA: {e}")
return None

def load_parsers():
if os.path.exists(LOCAL_PARSERS_FILE):
try:
with open(LOCAL_PARSERS_FILE, 'r') as f:
st.session_state['parsers'] = json.load(f)
logging.info("`parsers.json` loaded into session state.")
except json.JSONDecodeError:
            st.error("`parsers.json` is corrupted or not in valid JSON format.")
            st.sidebar.error("`parsers.json` is corrupted or not in valid JSON format.")
logging.error("`parsers.json` is corrupted or not in valid JSON format.")
except Exception as e:
            st.error(f"Unexpected error while loading `parsers.json`: {e}")
            st.sidebar.error(f"Unexpected error while loading `parsers.json`: {e}")
logging.error(f"Unexpected error while loading `parsers.json`: {e}")
else:
        st.error("`parsers.json` does not exist locally. Please download it from GitHub.")
        st.sidebar.error("`parsers.json` does not exist locally. Please download it from GitHub.")
logging.error("`parsers.json` does not exist locally.")

def save_parsers():
try:
with open(LOCAL_PARSERS_FILE, 'w') as f:
json.dump(st.session_state['parsers'], f, indent=4)
        st.success("`parsers.json` has been updated locally. Please upload it back to GitHub.")
        st.sidebar.success("`parsers.json` has been updated locally. Please upload it back to GitHub.")
logging.info("`parsers.json` has been updated locally.")
except Exception as e:
        st.error(f"Failed to save `parsers.json` locally: {e}")
        st.sidebar.error(f"Failed to save `parsers.json` locally: {e}")
logging.error(f"Failed to save `parsers.json` locally: {e}")

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
                st.experimental_rerun()  # Changed to rerun for immediate update
                st.experimental_rerun()  # Rerun to update the parsers list

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

            # Use a unique key for each delete button to prevent conflicts
            if st.button(f"Delete {parser_name}", key=f"delete_{parser_name}"):
                del st.session_state['parsers'][parser_name]
                save_parsers()
                st.success(f"Parser '{parser_name}' has been deleted.")
                st.experimental_rerun()  # Changed to rerun for immediate update
            # "Use this parser" Button
            use_parser = st.button("Use this parser", key=f"use_{parser_name}")
            if use_parser:
                st.session_state['selected_parser'] = parser_name
                st.session_state['active_menu'] = "Run Parser"
                st.experimental_rerun()

def flatten_json(y):
"""
   Flatten a nested JSON object.
   """
out = {}
order = []

def flatten(x, name=''):
if isinstance(x, dict):
for a in x:
flatten(x[a], name + a + '.')
elif isinstance(x, list):
i = 0
for a in x:
flatten(a, name + str(i) + '.')
i += 1
else:
out[name[:-1]] = x
order.append(name[:-1])
flatten(y)
return out, order

def generate_comparison_results(json1, json2):
"""
   Generate a new JSON object with tick or cross based on whether attributes match.
   """
flat_json1, order1 = flatten_json(json1)
flat_json2, _ = flatten_json(json2)

comparison_results = {}

for key in order1:
val1 = flat_json1.get(key, "N/A")
val2 = flat_json2.get(key, "N/A")
match = (val1 == val2)
comparison_results[key] = "✔" if match else "✘"

return comparison_results

def generate_comparison_df(json1, json2, comparison_results):
"""
   Generate a DataFrame comparing two JSON objects.
   """
flat_json1, order1 = flatten_json(json1)
flat_json2, _ = flatten_json(json2)

data = []
for key in order1:
val1 = flat_json1.get(key, "N/A")
val2 = flat_json2.get(key, "N/A")
match = comparison_results[key]
data.append([key, val1, val2, match])

df = pd.DataFrame(data, columns=['Attribute', 'Result with Extra Accuracy', 'Result without Extra Accuracy', 'Comparison'])
return df

def display_pdf(file):
    """
    Display a PDF file within the Streamlit app using an embedded iframe.
    """
    base64_pdf = base64.b64encode(file.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def run_parser(parsers):
st.subheader("Run OCR Parser")
if not parsers:
st.info("No parsers available. Please add a parser first.")
return

    # Pre-select parser if selected via "Use this parser" button
    if st.session_state['selected_parser']:
        default_parser = st.session_state['selected_parser']
    else:
        default_parser = parsers.keys()[0] if parsers else None

parser_names = list(parsers.keys())
    selected_parser = st.selectbox("Select Parser", parser_names)
    selected_parser = st.selectbox("Select Parser", parser_names, index=parser_names.index(default_parser) if default_parser else 0)
parser_info = parsers[selected_parser]

    # Update selected parser in session_state
    st.session_state['selected_parser'] = selected_parser

st.write(f"**Selected Parser:** {selected_parser}")
st.write(f"**Parser App ID:** {parser_info['parser_app_id']}")
st.write(f"**Extra Accuracy Required:** {'Yes' if parser_info['extra_accuracy'] else 'No'}")

    input_method = st.radio("Choose Input Method", ("Upload Image File", "Upload PDF File", "Enter Image URL"))
    # Input Method Selection using Styled Buttons
    st.markdown("### Choose Input Method")
    cols = st.columns(2)
    input_method = None

    if 'input_method' not in st.session_state:
        st.session_state['input_method'] = "Upload Image File"

    with cols[0]:
        upload_btn = st.button("Upload Image File", key="upload_btn")
        if upload_btn:
            st.session_state['input_method'] = "Upload Image File"

    with cols[1]:
        url_btn = st.button("Enter Image URL", key="url_btn")
        if url_btn:
            st.session_state['input_method'] = "Enter Image URL"

    input_method = st.session_state['input_method']
    st.write(f"**Current Input Method:** {input_method}")

image_paths = []
    pdf_paths = []
images = []
    pdf_files = []
temp_dirs = []
    pdf_pages = []

if input_method == "Upload Image File":
uploaded_files = st.file_uploader(
            "Choose image(s)...",
            type=["jpg", "jpeg", "png", "bmp", "gif", "tiff"],
            "Choose image(s) or PDF file(s)...",
            type=["jpg", "jpeg", "png", "bmp", "gif", "tiff", "pdf"],
accept_multiple_files=True
)
if uploaded_files:
for uploaded_file in uploaded_files:
                file_extension = os.path.splitext(uploaded_file.name)[1].lower()
try:
                    image = Image.open(uploaded_file)
                    images.append(image)
                    st.image(image, caption=uploaded_file.name, use_column_width=True)
                    temp_dir = tempfile.mkdtemp()
                    temp_dirs.append(temp_dir)
                    image_path = os.path.join(temp_dir, uploaded_file.name)
                    image.save(image_path)
                    image_paths.append(image_path)
                    if file_extension == ".pdf":
                        # Convert PDF to images
                        with tempfile.TemporaryDirectory() as temp_dir:
                            pdf_path = os.path.join(temp_dir, uploaded_file.name)
                            with open(pdf_path, "wb") as f:
                                f.write(uploaded_file.read())
                            pages = convert_from_path(pdf_path)
                            for i, page in enumerate(pages):
                                page_filename = f"{os.path.splitext(uploaded_file.name)[0]}_page_{i+1}.jpg"
                                page_path = os.path.join(temp_dir, page_filename)
                                page.save(page_path, 'JPEG')
                                images.append(page)
                                image_paths.append(page_path)
                                pdf_pages.append(page)
                                st.image(page, caption=page_filename, use_column_width=True)
                    else:
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
    elif input_method == "Upload PDF File":
        uploaded_pdfs = st.file_uploader(
            "Choose PDF file(s)...",
            type=["pdf"],
            accept_multiple_files=True
        )
        if uploaded_pdfs:
            for uploaded_pdf in uploaded_pdfs:
                try:
                    # Display PDF
                    display_pdf(uploaded_pdf)
                    uploaded_pdf.seek(0)  # Reset file pointer after reading
                    pdf_files.append(uploaded_pdf)
                    temp_dir = tempfile.mkdtemp()
                    temp_dirs.append(temp_dir)
                    pdf_path = os.path.join(temp_dir, uploaded_pdf.name)
                    with open(pdf_path, 'wb') as f:
                        f.write(uploaded_pdf.read())
                    pdf_paths.append(pdf_path)
                except Exception as e:
                    st.error(f"Error processing PDF {uploaded_pdf.name}: {e}")
                    logging.error(f"Error processing PDF {uploaded_pdf.name}: {e}")
    else:  # Enter Image URL
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
                        file_extension = os.path.splitext(url.split('?')[0])[1].lower()
                        if file_extension == ".pdf":
                            # Convert PDF to images
                            with tempfile.TemporaryDirectory() as temp_dir:
                                pdf_filename = f"{uuid.uuid4()}.pdf"
                                pdf_path = os.path.join(temp_dir, pdf_filename)
                                with open(pdf_path, 'wb') as f:
                                    f.write(response.content)
                                pages = convert_from_path(pdf_path)
                                for i, page in enumerate(pages):
                                    page_filename = f"page_{i+1}.jpg"
                                    page_path = os.path.join(temp_dir, page_filename)
                                    page.save(page_path, 'JPEG')
                                    images.append(page)
                                    image_paths.append(page_path)
                                    pdf_pages.append(page)
                                    st.image(page, caption=page_filename, use_column_width=True)
                        else:
                            image = Image.open(BytesIO(response.content))
                            images.append(image)
                            st.image(image, caption=os.path.basename(url.split('?')[0]), use_column_width=True)
                            temp_dir = tempfile.mkdtemp()
                            temp_dirs.append(temp_dir)
                            image_filename = os.path.basename(url.split('?')[0])
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

    # Clear previous OCR results if user provides new images
    if st.button("Clear Previous Results"):
        st.session_state['ocr_results'] = {
            'response_extra': None,
            'time_taken_extra': None,
            'response_no_extra': None,
            'time_taken_no_extra': None,
            'comparison_results': None,
            'comparison_table': None,
            'pdf_pages': []
        }
        st.session_state['selected_parser'] = None
        st.experimental_rerun()

if st.button("Run OCR"):
        if not image_paths and not pdf_paths:
        if not image_paths and not images:
st.error("Please provide at least one image or PDF to process.")
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

        def send_request(file_paths, extra_accuracy):
        def send_request(extra_accuracy):
local_headers = headers.copy()
local_form_data = form_data.copy()
if extra_accuracy:
local_form_data['extra_accuracy'] = 'true'

# List of files to upload
files = []
            for file_path in file_paths:
                _, file_ext = os.path.splitext(file_path.lower())
            for image_path in image_paths:
                _, file_ext = os.path.splitext(image_path.lower())
mime_types = {
'.jpg': 'image/jpeg',
'.jpeg': 'image/jpeg',
'.png': 'image/png',
'.bmp': 'image/bmp',
'.gif': 'image/gif',
                    '.tiff': 'image/tiff',
                    '.pdf': 'application/pdf'
                    '.tiff': 'image/tiff'
}
mime_type = mime_types.get(file_ext, 'application/octet-stream')
try:
                    files.append(('file', (os.path.basename(file_path), open(file_path, 'rb'), mime_type)))
                    files.append(('file', (os.path.basename(image_path), open(image_path, 'rb'), mime_type)))
except Exception as e:
                    st.error(f"Error opening file {file_path}: {e}")
                    logging.error(f"Error opening file {file_path}: {e}")
                    st.error(f"Error opening file {image_path}: {e}")
                    logging.error(f"Error opening file {image_path}: {e}")
return None, 0

try:
start_time = time.time()
logging.info(f"Sending POST request to {API_ENDPOINT} with Parser App ID: {local_form_data['parserApp']}, Extra Accuracy: {extra_accuracy}")
response = requests.post(API_ENDPOINT, headers=local_headers, data=local_form_data, files=files if files else None, timeout=120)
time_taken = time.time() - start_time
logging.info(f"Received response: {response.status_code} in {time_taken:.2f} seconds")
return response, time_taken
except requests.exceptions.RequestException as e:
logging.error(f"Error in API request: {e}")
st.error(f"Error in API request: {e}")
return None, 0
finally:
# Cleanup files
for _, file_tuple in files:
file_tuple[1].close()

with st.spinner("Processing OCR..."):
            response_extra_img, time_taken_extra_img = send_request(image_paths, True) if image_paths else (None, 0)
            response_extra_pdf, time_taken_extra_pdf = send_request(pdf_paths, True) if pdf_paths else (None, 0)
            response_no_extra_img, time_taken_no_extra_img = send_request(image_paths, False) if image_paths else (None, 0)
            response_no_extra_pdf, time_taken_no_extra_pdf = send_request(pdf_paths, False) if pdf_paths else (None, 0)
            response_extra, time_taken_extra = send_request(True)
            response_no_extra, time_taken_no_extra = send_request(False)

# Cleanup temporary directories
for temp_dir in temp_dirs:
try:
shutil.rmtree(temp_dir)
logging.info(f"Cleaned up temporary directory {temp_dir}")
except Exception as e:
logging.warning(f"Could not remove temporary directory {temp_dir}: {e}")

        # Combine responses and times
        responses_extra = [resp for resp in [response_extra_img, response_extra_pdf] if resp is not None]
        times_extra = [time_taken_extra_img, time_taken_extra_pdf]
        responses_no_extra = [resp for resp in [response_no_extra_img, response_no_extra_pdf] if resp is not None]
        times_no_extra = [time_taken_no_extra_img, time_taken_no_extra_pdf]

        # Process Extra Accuracy Responses
        if responses_extra:
            combined_response_extra = {}
            combined_time_extra = 0
            for resp, t in zip(responses_extra, times_extra):
                if resp.status_code == 200:
                    try:
                        combined_response_extra.update(resp.json())
                        combined_time_extra += t
                    except json.JSONDecodeError:
                        st.error("Failed to parse JSON response with Extra Accuracy.")
                        logging.error("Failed to parse JSON response with Extra Accuracy.")
                else:
                    st.error(f"Request with Extra Accuracy failed with status code: {resp.status_code}")
                    logging.error(f"Request with Extra Accuracy failed with status code: {resp.status_code}")
            success_extra = combined_response_extra != {}
        else:
            combined_response_extra = None
            combined_time_extra = 0
            success_extra = False

        # Process No Extra Accuracy Responses
        if responses_no_extra:
            combined_response_no_extra = {}
            combined_time_no_extra = 0
            for resp, t in zip(responses_no_extra, times_no_extra):
                if resp.status_code == 200:
                    try:
                        combined_response_no_extra.update(resp.json())
                        combined_time_no_extra += t
                    except json.JSONDecodeError:
                        st.error("Failed to parse JSON response without Extra Accuracy.")
                        logging.error("Failed to parse JSON response without Extra Accuracy.")
                else:
                    st.error(f"Request without Extra Accuracy failed with status code: {resp.status_code}")
                    logging.error(f"Request without Extra Accuracy failed with status code: {resp.status_code}")
            success_no_extra = combined_response_no_extra != {}
        # Store OCR results in session_state
        if response_extra and response_no_extra:
            st.session_state['ocr_results']['response_extra'] = response_extra
            st.session_state['ocr_results']['time_taken_extra'] = time_taken_extra
            st.session_state['ocr_results']['response_no_extra'] = response_no_extra
            st.session_state['ocr_results']['time_taken_no_extra'] = time_taken_no_extra

            if response_extra.status_code == 200 and response_no_extra.status_code == 200:
                try:
                    response_json_extra = response_extra.json()
                    response_json_no_extra = response_no_extra.json()

                    # Store comparison results
                    comparison_results = generate_comparison_results(response_json_extra, response_json_no_extra)
                    st.session_state['ocr_results']['comparison_results'] = comparison_results

                    # Store comparison table
                    comparison_table = generate_comparison_df(response_json_extra, response_json_no_extra, comparison_results)
                    st.session_state['ocr_results']['comparison_table'] = comparison_table

                except json.JSONDecodeError:
                    st.error("Failed to parse JSON response.")
                    st.text("Response with Extra Accuracy:\n" + response_extra.text)
                    st.text("Response without Extra Accuracy:\n" + response_no_extra.text)
            else:
                st.session_state['ocr_results']['comparison_results'] = None
                st.session_state['ocr_results']['comparison_table'] = None
else:
            combined_response_no_extra = None
            combined_time_no_extra = 0
            success_no_extra = False
            st.session_state['ocr_results']['response_extra'] = None
            st.session_state['ocr_results']['time_taken_extra'] = None
            st.session_state['ocr_results']['response_no_extra'] = None
            st.session_state['ocr_results']['time_taken_no_extra'] = None
            st.session_state['ocr_results']['comparison_results'] = None
            st.session_state['ocr_results']['comparison_table'] = None

    def display_ocr_results():
        ocr_results = st.session_state['ocr_results']
        response_extra = ocr_results['response_extra']
        time_taken_extra = ocr_results['time_taken_extra']
        response_no_extra = ocr_results['response_no_extra']
        time_taken_no_extra = ocr_results['time_taken_no_extra']
        comparison_results = ocr_results['comparison_results']
        comparison_table = ocr_results['comparison_table']
        pdf_pages = ocr_results['pdf_pages']

        if response_extra and response_no_extra:
            success_extra = response_extra.status_code == 200
            success_no_extra = response_no_extra.status_code == 200

        # Display Results
        if success_extra or success_no_extra:
# Create two columns for side-by-side display
col1, col2 = st.columns(2)

if success_extra:
                with col1:
                    st.expander(f"Results with Extra Accuracy - ⏱ {combined_time_extra:.2f}s").json(combined_response_extra)
                try:
                    response_json_extra = response_extra.json()
                    with col1:
                        st.expander(f"Results with Extra Accuracy - ⏱ {time_taken_extra:.2f}s").json(response_json_extra)
                except json.JSONDecodeError:
                    with col1:
                        st.error("Failed to parse JSON response with Extra Accuracy.")
                        logging.error("Failed to parse JSON response with Extra Accuracy.")
else:
with col1:
st.error("Request with Extra Accuracy failed.")
                    logging.error("Request with Extra Accuracy failed.")
                    logging.error(f"Request with Extra Accuracy failed with status code: {response_extra.status_code}")

if success_no_extra:
                with col2:
                    st.expander(f"Results without Extra Accuracy - ⏱ {combined_time_no_extra:.2f}s").json(combined_response_no_extra)
                try:
                    response_json_no_extra = response_no_extra.json()
                    with col2:
                        st.expander(f"Results without Extra Accuracy - ⏱ {time_taken_no_extra:.2f}s").json(response_json_no_extra)
                except json.JSONDecodeError:
                    with col2:
                        st.error("Failed to parse JSON response without Extra Accuracy.")
                        logging.error("Failed to parse JSON response without Extra Accuracy.")
else:
with col2:
st.error("Request without Extra Accuracy failed.")
                    logging.error("Request without Extra Accuracy failed.")
                    logging.error(f"Request without Extra Accuracy failed with status code: {response_no_extra.status_code}")

# Comparison JSON
st.subheader("Comparison JSON")
            if success_extra and success_no_extra:
                comparison_results = generate_comparison_results(combined_response_extra, combined_response_no_extra)
            if comparison_results:
st.expander("Comparison JSON").json(comparison_results)
else:
st.error("Cannot generate Comparison JSON as one or both OCR requests failed.")

# Comparison Table
st.subheader("Comparison Table")
            if success_extra and success_no_extra:
                comparison_results = generate_comparison_results(combined_response_extra, combined_response_no_extra)
                comparison_table = generate_comparison_df(combined_response_extra, combined_response_no_extra, comparison_results)

                if not comparison_table.empty:
                    gb = GridOptionsBuilder.from_dataframe(comparison_table)
                    gb.configure_pagination(paginationAutoPageSize=True)
                    gb.configure_side_bar()
                    gb.configure_selection('single')
                    grid_options = gb.build()

                    # Use a valid theme, e.g., 'streamlit'
                    AgGrid(comparison_table, gridOptions=grid_options, height=500, theme='streamlit', enable_enterprise_modules=True)
                else:
                    st.info("No common fields to compare in the OCR results.")
            if comparison_table is not None and not comparison_table.empty:
                gb = GridOptionsBuilder.from_dataframe(comparison_table)
                gb.configure_pagination(paginationAutoPageSize=True)
                gb.configure_side_bar()
                gb.configure_selection('single')
                grid_options = gb.build()

                # Use a valid theme, e.g., 'streamlit'
                AgGrid(comparison_table, gridOptions=grid_options, height=500, theme='streamlit', enable_enterprise_modules=True)
else:
st.error("Cannot display Comparison Table as one or both OCR requests failed.")

            # Display PDF pages if any
            if pdf_pages:
                st.subheader("Uploaded PDFs")
                for idx, page in enumerate(pdf_pages, start=1):
                    st.image(page, caption=f"PDF Page {idx}", use_column_width=True)

if success_extra and success_no_extra:
st.success("Both OCR requests completed successfully.")
else:
st.error("One or both OCR requests failed. Please check the logs for more details.")

    def run_parser_with_display(parsers):
        run_parser(parsers)
        display_ocr_results()

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
                margin: 5px;
            }
            .stButton>button:hover {
                background-color: #45a049;
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
                <li>Run parsers on images or PDFs</li>
            </ul>
        """, unsafe_allow_html=True)

        menu = ["List Parsers", "Run Parser", "Add Parser"]
        choice = st.sidebar.radio("Menu", menu, key='menu_selection')

        # Handle navigation based on session_state['active_menu']
        if st.session_state['active_menu']:
            current_menu = st.session_state['active_menu']
else:
            st.error("One or both OCR requests did not receive a valid response.")

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
            <li>Run parsers on images or PDFs</li>
        </ul>
    """, unsafe_allow_html=True)

    menu = ["List Parsers", "Run Parser", "Add Parser"]
    choice = st.sidebar.radio("Menu", menu)

    # Ensure this is only called at the start to load or get the latest parsers.
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
            current_menu = "List Parsers"

        # Ensure parsers are loaded
        if 'loaded' not in st.session_state:
            download_parsers_from_github()
            st.session_state['loaded'] = True

        if current_menu == "Add Parser" or choice == "Add Parser":
            add_new_parser()
        elif current_menu == "List Parsers" or choice == "List Parsers":
            list_parsers()
        elif current_menu == "Run Parser" or choice == "Run Parser":
            run_parser_with_display(st.session_state['parsers'])

        # GitHub Actions
        st.sidebar.header("GitHub Actions")
        if st.sidebar.button("Download Parsers"):
            download_parsers_from_github()

        if st.sidebar.button("Update Parsers File"):
            upload_parsers_to_github()

    if __name__ == "__main__":
        main()
