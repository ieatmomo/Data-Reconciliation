import streamlit as st
import pandas as pd
from utils.validators import get_system_info
from utils.api_client import upload_files_for_comparison

def render_file_upload_section(map_path):
    """Render the file upload and comparison section."""
    
    # File uploaders
    old_upload = st.sidebar.file_uploader("Upload Old File", type=["csv", "xls", "xlsx", "xml"])
    new_upload = st.sidebar.file_uploader("Upload New File", type=["csv", "xls", "xlsx", "xml"])
    
    if not (old_upload and new_upload):
        return
    
    # =============================================================================
    # FILE UPLOAD AND COMPARISON SECTION
    # =============================================================================

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
        result = upload_files_for_comparison(old_upload, new_upload, map_path)
        if result:
            st.session_state['auto_pk'] = result.get("primary_key", [])
            st.session_state['result'] = result
            st.session_state['primary_key'] = st.session_state['auto_pk']
            available_columns = result.get("available_columns", result.get("primary_key", []))
        else:
            st.session_state['auto_pk'] = []
            available_columns = []
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
            on_change=lambda: _run_comparison_with_pk(old_upload, new_upload, map_path)
        )

    # Show results if available
    if 'result' in st.session_state:
        _render_comparison_results()

def _run_comparison_with_pk(old_upload, new_upload, map_path):
    """Re-run comparison with selected primary keys."""
    pk = st.session_state.get('primary_key')
    result = upload_files_for_comparison(old_upload, new_upload, map_path, pk)
    if result:
        st.session_state['result'] = result

def _render_comparison_results():
    """Display comparison results."""
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