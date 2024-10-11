import os
import json
import requests
import time
import pandas as pd
import streamlit as st
import logging

# ocr_utils.py
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def flatten_json(y, separator='__', prefix=''):
    """
    Recursively flattens a nested JSON object into a flat dictionary.
    Uses '__' as a separator for clarity.
    """
    flat = {}
    if isinstance(y, dict):
        for key, value in y.items():
            new_key = f"{prefix}{key}" if prefix else key
            if isinstance(value, dict):
                flat.update(flatten_json(value, separator, new_key + separator))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        # Use 'Sr_No' as an identifier if available
                        identifier = item.get('Sr_No', i)
                        flat.update(flatten_json(item, separator, f"{new_key}{separator}{identifier}{separator}"))
                    else:
                        flat[f"{new_key}{separator}{i}"] = item
            else:
                flat[new_key] = value
    elif isinstance(y, list):
        for i, item in enumerate(y):
            if isinstance(item, dict):
                flat.update(flatten_json(item, separator, f"{prefix}{i}{separator}"))
            else:
                flat[f"{prefix}{i}"] = item
    else:
        flat[prefix] = y

    # Log the current state of the flattened JSON
    if prefix == '':
        logger.info("Flattened JSON Structure:")
        for k, v in flat.items():
            logger.info(f"{k}: {v}")

    return flat


# Function to generate comparison results (ignoring case differences)
def generate_comparison_results(json1, json2):
    """
    Generate comparison results by comparing two flattened JSON objects.
    """
    flat_json1, order1 = flatten_json(json1)
    flat_json2, _ = flatten_json(json2)

    comparison_results = {}
    for key in order1:
        val1 = flat_json1.get(key, "N/A")
        val2 = flat_json2.get(key, "N/A")

        # Convert all values to strings for consistent comparison
        val1_str = str(val1).strip().lower() if val1 is not None else ""
        val2_str = str(val2).strip().lower() if val2 is not None else ""

        match = (val1_str == val2_str)
        comparison_results[key] = "✔" if match else "✘"
    
    return comparison_results

# Function to generate a DataFrame for the comparison
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
        match = comparison_results.get(key, "✘")  # Default to mismatch if key not found
        data.append([key, val1, val2, match])

    df = pd.DataFrame(data, columns=['Attribute', 'Result with Extra Accuracy', 'Result without Extra Accuracy', 'Comparison'])
    return df

# Function to generate a DataFrame with only mismatched fields
def generate_mismatch_df(json1, json2, comparison_results):
    """
    Generate a DataFrame showing only the mismatched fields between the two JSONs.
    """
    flat_json1, order1 = flatten_json(json1)
    flat_json2, _ = flatten_json(json2)

    data = []
    for key in order1:
        val1 = flat_json1.get(key, "N/A")
        val2 = flat_json2.get(key, "N/A")
        if comparison_results[key] == "✘":  # Only include mismatched fields
            data.append([key, val1, val2])

    # Create a DataFrame with only the mismatched fields
    df = pd.DataFrame(data, columns=['Field', 'Result with Extra Accuracy', 'Result without Extra Accuracy'])
    return df

# Function to send OCR request
def send_request(image_paths, headers, form_data, extra_accuracy, API_ENDPOINT):
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
            '.tiff': 'image/tiff',
            '.pdf': 'application/pdf'
        }
        mime_type = mime_types.get(file_ext, 'application/octet-stream')
        try:
            files.append(('file', (os.path.basename(image_path), open(image_path, 'rb'), mime_type)))
        except Exception as e:
            st.error(f"Error opening file {image_path}: {e}")
            return None, 0

    try:
        start_time = time.time()
        response = requests.post(API_ENDPOINT, headers=local_headers, data=local_form_data, files=files if files else None, timeout=120)
        time_taken = time.time() - start_time
        return response, time_taken
    except requests.exceptions.RequestException as e:
        st.error(f"Error in OCR request: {e}")
        return None, 0
    finally:
        # Cleanup files
        for _, file_tuple in files:
            file_tuple[1].close()
