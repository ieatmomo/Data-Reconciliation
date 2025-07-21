import streamlit as st
import requests
import plotly.graph_objects as go
import json
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

        response = requests.get("http://localhost:5000/history", params={
            "system": result.get("system_name"),
            "primary_key_used": ','.join(result.get("primary_key", []))
            
        })
        st.subheader(f"Historical Data for {result.get('system_name', 'Unknown')}")
        if response.ok:
            graph_data = response.json()
            system_name = graph_data.get('system_name', result.get("system_name", "Unknown"))

            # Create two separate charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Exception Count Bar Chart
                fig_exceptions = go.Figure()
                fig_exceptions.add_trace(go.Bar(
                    x=graph_data['dates'],
                    y=graph_data['exception_counts'],
                    name='Exception Count',
                    marker_color='lightcoral'
                ))
                
                fig_exceptions.update_layout(
                    title=f'Exception Count Trend - {system_name.title()}',
                    xaxis=dict(
                        title='Date',
                        type='category'
                    ),
                    yaxis=dict(
                        title='Number of Exceptions',
                        range=[0, max(graph_data['exception_counts']) * 1.1]
                    ),
                    height=400
                )
                st.plotly_chart(fig_exceptions, use_container_width=True)
            
            with col2:
                # Match Rate Line Chart
                fig_match_rate = go.Figure()
                fig_match_rate.add_trace(go.Scatter(
                    x=graph_data['dates'],
                    y=graph_data['match_rates'],
                    mode='lines+markers',
                    name='Match Rate %',
                    line=dict(color='blue', width=3),
                    marker=dict(size=8)
                ))
                
                fig_match_rate.update_layout(
                    title=f'Match Rate Trend - {system_name.title()}',
                    xaxis=dict(
                        title='Date',
                        type='category'
                    ),
                    yaxis=dict(
                        title='Match Rate (%)',
                        range=[0, 100]
                    ),
                    height=400
                )
                st.plotly_chart(fig_match_rate, use_container_width=True)
        else:
            st.error(f"Failed to load historical data: {response.status_code}")