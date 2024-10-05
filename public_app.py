import streamlit as st

def main():
    # Set page config
    st.set_page_config(page_title="FRACTO OCR - Public Page", layout="wide")

    # Title and Information about Fracto OCR
    st.title("Welcome to Fracto OCR")
    st.markdown("""
    **Fracto OCR** is an advanced document processing solution designed to help businesses streamline document recognition and extraction tasks.

    With Fracto OCR, you can:
    - Run custom parsers on document images.
    - Automate document handling processes with AI-driven accuracy.
    - Benefit from integration-ready services that simplify automation.

    Reach out to us for more information or collaboration opportunities.
    """)

    # Button to navigate to the team app
    if st.button("Go to Team App"):
        # Generate the link to the team app
        team_app_url = "https://fracto-ocr.streamlit.app/teamapp"
        st.markdown(f"[Click here to go to the Team App]({team_app_url})")

if __name__ == "__main__":
    main()

