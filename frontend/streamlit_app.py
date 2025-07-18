import streamlit as st
import requests
import pandas as pd

st.title("Reconciliation Tool")

# --- Sidebar Inputs ---
st.sidebar.header("Configuration")
map_path = st.sidebar.text_input("Mapping YAML Path", "mapping.yaml")
old_upload = st.sidebar.file_uploader("Upload Old File", type=["csv", "xls", "xlsx", "xml"])
new_upload = st.sidebar.file_uploader("Upload New File", type=["csv", "xls", "xlsx", "xml"])

def run_comparison():
    old_upload.seek(0)
    new_upload.seek(0)
    files = {
        'old': old_upload,
        'new': new_upload,
        'mapping_path': (None, map_path)
    }
    data = {}
    pk = st.session_state.get('primary_key')
    if pk:
        data['primary_key'] = ','.join(pk)
    response = requests.post("http://localhost:5000/upload", files=files, data=data)
    if response.ok:
        st.session_state['result'] = response.json()
    else:
        st.error(response.text)

if old_upload and new_upload:
    # Normalize columns to lowercase
    df_old = pd.read_csv(old_upload) if old_upload.name.endswith('.csv') else pd.read_excel(old_upload)
    df_new = pd.read_csv(new_upload) if new_upload.name.endswith('.csv') else pd.read_excel(new_upload)
    df_old.columns = [c.strip().lower() for c in df_old.columns]
    df_new.columns = [c.strip().lower() for c in df_new.columns]
    common_cols = list(set(df_old.columns) & set(df_new.columns))

    # Auto-detect PK only once per file upload
    if 'auto_pk' not in st.session_state:
        old_upload.seek(0)
        new_upload.seek(0)
        files = {
            'old': old_upload,
            'new': new_upload,
            'mapping_path': (None, map_path)
        }
        response = requests.post("http://localhost:5000/upload", files=files)
        if response.ok:
            st.session_state['auto_pk'] = response.json().get("primary_key", [])
            st.session_state['result'] = response.json()
            st.session_state['primary_key'] = st.session_state['auto_pk']
        else:
            st.session_state['auto_pk'] = []
            st.error(response.text)

    # Sidebar PK selection (default to auto-detected), triggers update on change
    st.sidebar.multiselect(
        "Select Primary Key(s)",
        options=common_cols,
        default=st.session_state.get('auto_pk', []),
        key='primary_key',
        on_change=run_comparison
    )

    # Show results if available
    if 'result' in st.session_state:
        result = st.session_state['result']
        st.metric("Match Rate", f"{result['match_pct']}%")
        st.write("Primary Key(s) Used:", ", ".join(map(str, result.get("primary_key", []))))
        num_exceptions = len(result.get("exceptions", []))
        st.write(f"Number of Exceptions: {num_exceptions}")
        st.subheader("Exceptions")
        exceptions_df = pd.DataFrame(result['exceptions'])
        desired_order = ['id', 'field', 'old', 'new']
        columns_to_show = [col for col in desired_order if col in exceptions_df.columns]
        st.dataframe(exceptions_df[columns_to_show], height=400, use_container_width=True)
