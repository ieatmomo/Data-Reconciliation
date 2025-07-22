import streamlit as st
from components.file_upload import render_file_upload_section
from components.historical_browser import render_historical_browser

st.title("Reconciliation Tool")

# --- Sidebar Configuration ---
st.sidebar.header("Configuration")
map_path = st.sidebar.text_input("Mapping YAML Path", "mapping.yaml")

# Refresh Dashboard Button
if st.sidebar.button("🔄 Refresh Dashboard", help="Clear all results and refresh the dashboard"):
    # Clear all session state except file uploads
    keys_to_clear = ['auto_pk', 'result', 'primary_key', 'current_files']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# Render main sections
render_file_upload_section(map_path)
render_historical_browser()