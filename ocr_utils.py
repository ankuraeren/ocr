# ocr_utils.py

import os
import json
import requests
import time
import pandas as pd
import streamlit as st
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for detailed logs
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
                flat[f"{prefix}{separator}{i}"] = item
    else:
        flat[prefix] = y

    # Log the current state of the flattened JSON
    if prefix == '':
        logger.info("Flattened JSON Structure:")
        for k, v in flat.items():
            logger.info(f"{k}: {v}")

    return flat

def generate_comparison_results(json1, json2):
    """
    Generate comparison results by comparing two flattened JSON objects.
    Handles both numerical and string comparisons.
    """
    flat_json1 = flatten_json(json1)
    flat_json2 = flatten_json(json2)

    all_keys = set(flat_json1.keys()).union(set(flat_json2.keys()))

    comparison_results = {}
    for key in all_keys:
        val1 = flat_json1.get(key, "N/A")
        val2 = flat_json2.get(key, "N/A")

        # Log the values being compared
        logger.debug(f"Comparing key: {key}")
        logger.debug(f"Value with Extra Accuracy: {val1}")
        logger.debug(f"Value without Extra Accuracy: {val2}")

        # Special handling for specific fields
        if key.endswith("cheque_date"):
            # Example: Ensure date formats are consistent
            try:
                from dateutil import parser
                date1 = parser.parse(val1).date()
                date2 = parser.parse(val2).date()
                match = (date1 == date2)
                logger.debug(f"Date comparison: {date1} == {date2} -> {match}")
            except Exception as e:
                logger.error(f"Error parsing dates for key {key}: {e}")
                match = False
        else:
            # Handle numerical comparisons
            try:
                val1_num = float(val1)
                val2_num = float(val2)
                match = (val1_num == val2_num)
                logger.debug(f"Numerical comparison: {val1_num} == {val2_num} -> {match}")
            except (ValueError, TypeError):
                # Fallback to string comparison
                val1_str = str(val1).strip().lower() if val1 is not None else ""
                val2_str = str(val2).strip().lower() if val2 is not None else ""
                match = (val1_str == val2_str)
                logger.debug(f"String comparison: '{val1_str}' == '{val2_str}' -> {match}")

        comparison_results[key] = "✔" if match else "✘"

    return comparison_results

def generate_comparison_df(json1, json2, comparison_results):
    """
    Generate a DataFrame comparing two JSON objects.
    """
    flat_json1 = flatten_json(json1)
    flat_json2 = flatten_json(json2)

    data = []
    all_keys = set(flat_json1.keys()).union(set(flat_json2.keys()))  # Union of keys from both JSONs
    for key in all_keys:
        val1 = flat_json1.get(key, "N/A")
        val2 = flat_json2.get(key, "N/A")
        match = comparison_results.get(key, "✘")  # Default to mismatch if key not found
        data.append([key, val1, val2, match])

    df = pd.DataFrame(data, columns=['Attribute', 'Result with Extra Accuracy', 'Result without Extra Accuracy', 'Comparison'])
    return df

def generate_mismatch_df(json1, json2, comparison_results):
    """
    Generate a DataFrame showing only the mismatched fields between the two JSONs.
    """
    flat_json1 = flatten_json(json1)
    flat_json2 = flatten_json(json2)

    data = []
    all_keys = set(flat_json1.keys()).union(set(flat_json2.keys()))
    for key in all_keys:
        val1 = flat_json1.get(key, "N/A")
        val2 = flat_json2.get(key, "N/A")
        if comparison_results.get(key, "✘") == "✘":  # Only include mismatched fields
            data.append([key, val1, val2, comparison_results.get(key, "✘")])

    # Create a DataFrame with only the mismatched fields
    df = pd.DataFrame(data, columns=['Field', 'Result with Extra Accuracy', 'Result without Extra Accuracy', 'Comparison'])
    return df

def send_request(image_paths, headers, form_data, extra_accuracy, API_ENDPOINT):
    """
    Send OCR request to the API endpoint with the given parameters.
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
        response = requests.post(API_ENDPOINT, headers=local_headers, data=local_form_data, files=files if files else None, timeout=1200)
        time_taken = time.time() - start_time
        return response, time_taken
    except requests.exceptions.RequestException as e:
        st.error(f"Error in OCR request: {e}")
        return None, 0
    finally:
        # Cleanup files
        for _, file_tuple in files:
            file_tuple[1].close()
