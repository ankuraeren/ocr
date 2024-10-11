# ocr_runner.py

import os
import json
import requests
import time
import pandas as pd
import streamlit as st
from ocr_utils import send_request, generate_comparison_results, generate_comparison_df, generate_mismatch_df, flatten_json
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

# Main OCR parser function
def run_parser(parsers):
    st.subheader("Run OCR Parser")
    if not parsers:
        st.info("No parsers available. Please add a parser first.")
        return

    # Add custom CSS for horizontal, scrollable radio buttons
    st.markdown("""
        <style>
        .stRadio [role=radiogroup] {
            display: flex;
            flex-direction: row;
            overflow-x: auto;
            gap: 10px;
        }
        div[role='radiogroup'] label div[data-testid='stMarkdownContainer'] {
            font-size: 18px;
            font-weight: bold;
            color: #FFFFFF;
        }
        div[role='radiogroup'] label {
            background-color: #2B2B2B;
            padding: 10px 15px;
            border-radius: 12px;
            border: 1px solid #3B3B3B;
            cursor: pointer;
            white-space: nowrap;
        }
        div[role='radiogroup'] label:hover {
            background-color: #474747;
        }
        div[role='radiogroup'] input[type='radio']:checked + label {
            background-color: #FF5F5F;
            border-color: #FF5F5F;
        }
        div[role='radiogroup'] input[type='radio']:checked + label div[data-testid='stMarkdownContainer'] {
            color: #FFFFFF;
        }

        /* Hide the 200MB file size limit text */
        div[title~="Limit"] {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Convert parser selection into horizontal scrollable radio buttons
    parser_names = list(parsers.keys())
    selected_parser = st.radio("Select Parser", parser_names)
    parser_info = parsers[selected_parser]

    st.write(f"**Selected Parser:** {selected_parser}")
    st.write(f"**Extra Accuracy Required:** {'Yes' if parser_info['extra_accuracy'] else 'No'}")

    file_paths = []
    temp_dirs = []

    # Add a note to the user about the file size limit
    st.markdown("**Note:** Please upload an image or PDF file not exceeding **20MB**.")

    # File uploader with file size limit
    uploaded_file = st.file_uploader(
        "Choose an image or PDF file... (Limit 20MB per file)", 
        type=["jpg", "jpeg", "png", "pdf"], 
        accept_multiple_files=False
    )
    
    if uploaded_file:
        if uploaded_file.size > 20 * 1024 * 1024:  # 20 MB limit
            st.error("File size exceeds the 20 MB limit. Please upload a smaller file.")
            return
        try:
            if uploaded_file.type == "application/pdf":
                # Handle PDF files
                temp_dir = tempfile.mkdtemp()
                temp_dirs.append(temp_dir)
                pdf_path = os.path.join(temp_dir, uploaded_file.name)

                with open(pdf_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Display PDF filename
                st.markdown(f"**Uploaded PDF:** {uploaded_file.name}")
                file_paths.append(pdf_path)

            else:
                # Handle image files
                image = Image.open(uploaded_file)
                st.image(image, caption=uploaded_file.name, use_column_width=True)
                temp_dir = tempfile.mkdtemp()
                temp_dirs.append(temp_dir)
                image_path = os.path.join(temp_dir, uploaded_file.name)
                image.save(image_path)
                file_paths.append(image_path)

        except Exception as e:
            st.error(f"Error processing file {uploaded_file.name}: {e}")

    # Run OCR button
    if st.button("Run OCR"):
        if not file_paths:
            st.error("Please provide at least one image or PDF.")
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

        API_ENDPOINT = st.secrets["api"]["endpoint"]

        with st.spinner("Processing OCR..."):
            response_extra, time_taken_extra = send_request(file_paths, headers, form_data, True, API_ENDPOINT)
            response_no_extra, time_taken_no_extra = send_request(file_paths, headers, form_data, False, API_ENDPOINT)

        # Cleanup temporary directories
        for temp_dir in temp_dirs:
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                st.warning(f"Could not remove temporary directory {temp_dir}: {e}")

        if response_extra and response_no_extra:
            success_extra = response_extra.status_code == 200
            success_no_extra = response_no_extra.status_code == 200

            # Display results in two columns
            col1, col2 = st.columns(2)

            if success_extra:
                try:
                    response_json_extra = response_extra.json()
                    with col1:
                        st.expander(f"Results with Extra Accuracy - ⏱ {time_taken_extra:.2f}s").json(response_json_extra)
                except json.JSONDecodeError:
                    with col1:
                        st.error("Failed to parse JSON response with Extra Accuracy.")
            else:
                with col1:
                    st.error(f"Request with Extra Accuracy failed. Status code: {response_extra.status_code}")

            if success_no_extra:
                try:
                    response_json_no_extra = response_no_extra.json()
                    with col2:
                        st.expander(f"Results without Extra Accuracy - ⏱ {time_taken_no_extra:.2f}s").json(response_json_no_extra)
                except json.JSONDecodeError:
                    with col2:
                        st.error("Failed to parse JSON response without Extra Accuracy.")
            else:
                with col2:
                    st.error(f"Request without Extra Accuracy failed. Status code: {response_no_extra.status_code}")

            if success_extra and success_no_extra:
                # Generate comparison results
                comparison_results = generate_comparison_results(response_json_extra, response_json_no_extra)
                comparison_table = generate_comparison_df(response_json_extra, response_json_no_extra, comparison_results)
                comparison_table['Comparison'] = comparison_table['Comparison'].astype(str)  # Ensure it's string

                # Display mismatched fields in a table
                st.subheader("Mismatched Fields")
                mismatch_df = generate_mismatch_df(response_json_extra, response_json_no_extra, comparison_results)
                st.dataframe(mismatch_df)

                # Display the comparison table using AgGrid with Tree Data
                st.subheader("Comparison Table")

                # Prepare data for Tree Data
                def prepare_tree_data(df):
                    tree_data = []
                    for _, row in df.iterrows():
                        # Split the attribute into parts
                        parts = row['Attribute'].split('_')
                        current_level = tree_data
                        for i, part in enumerate(parts):
                            # Check if the part already exists
                            existing = next((item for item in current_level if item['Attribute'] == part), None)
                            if not existing:
                                new_node = {'Attribute': part}
                                if i == len(parts) - 1:
                                    # Leaf node
                                    new_node['Result with Extra Accuracy'] = row['Result with Extra Accuracy']
                                    new_node['Result without Extra Accuracy'] = row['Result without Extra Accuracy']
                                    new_node['Comparison'] = row['Comparison']
                                else:
                                    new_node['children'] = []
                                current_level.append(new_node)
                                existing = new_node
                            current_level = existing.get('children', [])
                    return tree_data

                tree_data = prepare_tree_data(comparison_table)

                # Define grid options
                gb = GridOptionsBuilder.from_dataframe(comparison_table)
                gb.configure_pagination(paginationAutoPageSize=True)
                gb.configure_side_bar()
                gb.configure_selection('single')

                # Enable Tree Data
                gb.configure_tree_data(column='Attribute', groupSelectsChildren=True)
                gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, tree=True)

                # Add custom cell renderer for 'Comparison' column
                comparison_renderer = JsCode("""
                function(params) {
                    if (params.value === '✔') {
                        return '<span style="color: green;">✔</span>';
                    } else {
                        return '<span style="color: red;">✘</span>';
                    }
                }
                """)

                gb.configure_column("Comparison", header_name="Comparison", cellRenderer=comparison_renderer, sortable=True, filter=True)

                grid_options = gb.build()

                AgGrid(
                    tree_data,
                    gridOptions=grid_options,
                    enable_enterprise_modules=True,
                    height=600,
                    width='100%',
                    theme='streamlit',
                    allow_unsafe_jscode=True  # Enable JavaScript
                )

                # Display the full comparison JSON after the table
                st.subheader("Comparison JSON")
                st.expander("Comparison JSON").json(comparison_results)

            else:
                st.error("Comparison failed. One or both requests were unsuccessful.")
        else:
            st.error("Comparison failed. One or both requests were unsuccessful.")
