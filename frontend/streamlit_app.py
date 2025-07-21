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

def load_available_systems():
    """Load available systems from the database."""
    try:
        response = requests.get("http://localhost:5000/systems")
        if response.ok:
            return response.json().get("systems", [])
        else:
            st.error("Failed to load available systems")
            return []
    except Exception as e:
        st.error(f"Error loading systems: {e}")
        return []

def display_historical_charts(selected_system, selected_pk=None):
    """Display historical charts for the selected system."""
    if not selected_system:
        return
    
    # Get historical data
    params = {"system": selected_system}
    if selected_pk:
        params["primary_key_used"] = selected_pk
    
    response = requests.get("http://localhost:5000/history", params=params)
    
    if response.ok:
        graph_data = response.json()
        if graph_data.get('dates'):
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
                    title=f'Exception Count Trend - {selected_system.title()}',
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
                    title=f'Match Rate Trend - {selected_system.title()}',
                    xaxis=dict(title='Date', type='category'),
                    yaxis=dict(title='Match Rate (%)', range=[0, 100]),
                    height=400
                )
                st.plotly_chart(fig_match_rate, use_container_width=True)
                
            # Show summary stats
            avg_match_rate = sum(graph_data['match_rates'])/len(graph_data['match_rates']) if graph_data['match_rates'] else 0
            total_exceptions = sum(graph_data['exception_counts']) if graph_data['exception_counts'] else 0
            
            st.markdown(f"""
            **📊 Summary for {selected_system.title()}:**
            - **Total Runs**: {len(graph_data['dates'])}
            - **Average Match Rate**: {avg_match_rate:.1f}%
            - **Total Exceptions**: {total_exceptions}
            - **Date Range**: {graph_data['dates'][0]} to {graph_data['dates'][-1]}
            """)
        else:
            st.info(f"No historical data available for system: {selected_system}")
    else:
        st.error(f"Failed to load historical data: {response.status_code}")

# =============================================================================
# FILE UPLOAD AND COMPARISON SECTION
# =============================================================================

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
            
            # Get primary key columns and create dynamic column order
            pk_columns = result.get("primary_key", [])
            
            # Start with primary key columns, then add field, old, new
            column_order = pk_columns.copy()
            for col in ['field', 'old', 'new']:
                if col in exceptions_df.columns and col not in column_order:
                    column_order.append(col)
            
            # Add any remaining columns
            for col in exceptions_df.columns:
                if col not in column_order:
                    column_order.append(col)
            
            # Filter to only include columns that actually exist
            columns_to_show = [col for col in column_order if col in exceptions_df.columns]
            
            st.dataframe(exceptions_df[columns_to_show], height=400, use_container_width=True)
            st.caption(f"Primary Key(s): {', '.join(pk_columns)}")

# =============================================================================
# HISTORICAL DATA BROWSER SECTION
# =============================================================================

st.header("📈 Historical Data Browser")
st.markdown("Browse historical reconciliation data for any system in the database.")

# Load available systems
available_systems = load_available_systems()

if available_systems:
    # System selection
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_system = st.selectbox(
            "Select System:",
            options=[""] + available_systems,
            index=0,
            help="Choose a system to view its historical reconciliation data"
        )
    
    with col2:
        if selected_system:
            # Get system details to show available primary keys
            try:
                response = requests.get(f"http://localhost:5000/system_details/{selected_system}")
                if response.ok:
                    system_details = response.json()
                    available_pks = system_details.get("primary_keys", [])
                    
                    if len(available_pks) > 1:
                        selected_pk = st.selectbox(
                            "Primary Key Filter:",
                            options=["All"] + available_pks,
                            help="Filter by specific primary key combination"
                        )
                        selected_pk = None if selected_pk == "All" else selected_pk
                    else:
                        selected_pk = None
                        if available_pks:
                            st.info(f"Primary Key: {available_pks[0]}")
                else:
                    selected_pk = None
                    st.error("Failed to load system details")
            except Exception as e:
                selected_pk = None
                st.error(f"Error: {e}")

    # Display historical data for selected system
    if selected_system:
        # Display charts
        display_historical_charts(selected_system, selected_pk)
        
        # Show historical exception records in a table
        st.subheader(f"📋 Exception Records for {selected_system.title()}")
        
        try:
            # Get historical data to extract exception records
            params = {"system": selected_system}
            if selected_pk:
                params["primary_key_used"] = selected_pk
            
            response = requests.get("http://localhost:5000/history", params=params)
            
            if response.ok:
                graph_data = response.json()
                
                if graph_data.get('dates'):
                    # Create a summary table of all runs
                    summary_data = []
                    for i, date in enumerate(graph_data['dates']):
                        summary_data.append({
                            'Date': date,
                            'Match Rate (%)': graph_data['match_rates'][i],
                            'Exception Count': graph_data['exception_counts'][i],
                            'Status': '✅ Good' if graph_data['match_rates'][i] >= 95 else '⚠️ Check Required' if graph_data['match_rates'][i] >= 90 else '❌ Issues'
                        })
                    
                    summary_df = pd.DataFrame(summary_data)
                    
                    # Display the summary table
                    st.dataframe(
                        summary_df,
                        height=300,
                        use_container_width=True,
                        column_config={
                            "Date": st.column_config.DateColumn("Date"),
                            "Match Rate (%)": st.column_config.NumberColumn("Match Rate (%)", format="%.1f"),
                            "Exception Count": st.column_config.NumberColumn("Exception Count"),
                            "Status": st.column_config.TextColumn("Status")
                        }
                    )
                    
                    # Download option
                    csv_data = summary_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Historical Data as CSV",
                        data=csv_data,
                        file_name=f"historical_data_{selected_system}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info(f"No historical data found for system: {selected_system}")
            else:
                st.error("Failed to load historical data")
                
        except Exception as e:
            st.error(f"Error loading historical data: {e}")
    
else:
    st.info("🔍 No systems found in the database. Upload some files to start building historical data!")
    st.markdown("""
    **To get started:**
    1. Upload your first set of files above
    2. Run a comparison
    3. Come back here to view historical trends
    """)