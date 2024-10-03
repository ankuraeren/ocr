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
