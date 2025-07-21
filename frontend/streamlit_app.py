import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd

st.title("Reconciliation Tool")

# --- Sidebar Inputs ---
st.sidebar.header("Configuration")
map_path = st.sidebar.text_input("Mapping YAML Path", "mapping.yaml")
old_upload = st.sidebar.file_uploader("Upload Old File", type=["csv", "xls", "xlsx", "xml"])
new_upload = st.sidebar.file_uploader("Upload New File", type=["csv", "xls", "xlsx", "xml"])

def validate_same_system(file1_name, file2_name):
    """
    Check if both files belong to the same system by comparing the first part of filename.
    Returns (is_valid, system_name, error_message)
    """
    try:
        # Remove file extensions
        name1 = file1_name.rsplit('.', 1)[0]  # Remove extension
        name2 = file2_name.rsplit('.', 1)[0]  # Remove extension
        
        # Split by common delimiters (underscore, hyphen, space)
        delimiters = ['_', '-', ' ']
        
        system1 = name1
        system2 = name2
        
        # Try each delimiter to find the system name
        for delimiter in delimiters:
            if delimiter in name1 and delimiter in name2:
                system1 = name1.split(delimiter)[0].lower().strip()
                system2 = name2.split(delimiter)[0].lower().strip()
                break
        
        # Check if systems match
        if system1 == system2:
            return True, system1, None
        else:
            return False, None, f"File system mismatch: '{system1}' vs '{system2}'. Both files should belong to the same system."
    
    except Exception as e:
        return False, None, f"Error validating file names: {str(e)}"

def get_system_info(file1_name, file2_name):
    """
    Extract system information from filenames for display.
    """
    is_valid, system_name, error = validate_same_system(file1_name, file2_name)
    
    if is_valid:
        return {
            "valid": True,
            "system": system_name,
            "file1_display": file1_name,
            "file2_display": file2_name,
            "message": f"✅ Both files belong to system: '{system_name}'"
        }
    else:
        return {
            "valid": False,
            "system": None,
            "file1_display": file1_name,
            "file2_display": file2_name,
            "message": f"❌ {error}"
        }

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
    # Validate that files belong to the same system
    system_info = get_system_info(old_upload.name, new_upload.name)
    
    # Display system validation result
    if system_info["valid"]:
        st.success(system_info["message"])
        st.info(f"📁 Old File: {system_info['file1_display']}")
        st.info(f"📁 New File: {system_info['file2_display']}")
    else:
        st.error(system_info["message"])
        st.warning("Please upload files that belong to the same system.")
        st.info(f"📁 Old File: {system_info['file1_display']}")
        st.info(f"📁 New File: {system_info['file2_display']}")
        
        # Show help message
        st.markdown("""
        **File Naming Examples:**
        - ✅ `products_old.csv` and `products_new.csv` → System: 'products'
        - ✅ `inventory-2024.xlsx` and `inventory-2025.xlsx` → System: 'inventory'
        - ✅ `sales old.xml` and `sales new.xml` → System: 'sales'
        - ❌ `products_old.csv` and `inventory_new.csv` → Different systems
        """)
        
        # Stop processing if validation fails
        st.stop()

    # Create a unique key for the current file combination
    file_key = f"{old_upload.name}_{new_upload.name}_{old_upload.size}_{new_upload.size}"
    
    # Clear session state if files have changed
    if st.session_state.get('current_files') != file_key:
        # Clear all previous state when new files are uploaded
        for key in ['auto_pk', 'result', 'primary_key', 'current_files']:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state['current_files'] = file_key

    # Auto-detect PK only once per file upload
    if 'auto_pk' not in st.session_state:
        old_upload.seek(0)
        new_upload.seek(0)
        files = {
            'old': old_upload,
            'new': new_upload,
            'mapping_path': (None, map_path)
        }
        # Call upload WITHOUT a primary key to trigger auto-detection
        response = requests.post("http://localhost:5000/upload", files=files)
        if response.ok:
            result = response.json()
            st.session_state['auto_pk'] = result.get("primary_key", [])
            st.session_state['result'] = result
            st.session_state['primary_key'] = st.session_state['auto_pk']
            
            # Get available columns from backend response
            available_columns = result.get("available_columns", result.get("primary_key", []))
        else:
            st.session_state['auto_pk'] = []
            available_columns = []
            st.error(response.text)
    else:
        # Get available columns from existing result
        result = st.session_state.get('result', {})
        available_columns = result.get("available_columns", result.get("primary_key", []))

    # Sidebar PK selection (default to auto-detected), triggers update on change
    if available_columns:
        st.sidebar.multiselect(
            "Select Primary Key(s)",
            options=available_columns,
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
        
        if result.get("exceptions"):
            st.subheader("Exceptions")
            exceptions_df = pd.DataFrame(result['exceptions'])
            desired_order = ['id', 'field', 'old', 'new']
            columns_to_show = [col for col in desired_order if col in exceptions_df.columns]
            st.dataframe(exceptions_df[columns_to_show], height=400, use_container_width=True)

        # Historical data
        response = requests.get("http://localhost:5000/history", params={
            "system": result.get("system_name"),
            "primary_key_used": ','.join(result.get("primary_key", []))
        })
        st.subheader(f"Historical Data for {result.get('system_name', 'Unknown')}")
        if response.ok:
            graph_data = response.json()
            if graph_data.get('dates'):
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
                        xaxis=dict(title='Date', type='category'),
                        yaxis=dict(
                            title='Number of Exceptions',
                            range=[0, max(graph_data['exception_counts']) * 1.1] if graph_data['exception_counts'] else [0, 1]
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
                        xaxis=dict(title='Date', type='category'),
                        yaxis=dict(title='Match Rate (%)', range=[0, 100]),
                        height=400
                    )
                    st.plotly_chart(fig_match_rate, use_container_width=True)
            else:
                st.info("No historical data available yet.")
        else:
            st.error(f"Failed to load historical data: {response.status_code}")