import streamlit as st
import pandas as pd
from utils.validators import get_system_info
from utils.api_client import upload_files_for_comparison, reject_exceptions, get_rejected_exceptions, recalculate_match_rate

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
    """Display comparison results with exception management."""
    result = st.session_state['result']
    
    # Extract system info for API calls
    system_name = result.get('system_name', 'unknown')
    analysis_id = result.get('analysis_id')  # This needs to be added to backend response
    
    # Display basic metrics
    col1, col2, col3 = st.columns(3)
    
    # Get rejected exceptions for accurate counts
    rejected_ids = []
    if analysis_id:
        rejected_response = get_rejected_exceptions(system_name, analysis_id)
        rejected_ids = rejected_response.get("rejected_ids", [])
    
    # Calculate current metrics
    original_exception_count = len(result.get("exceptions", []))
    remaining_exception_count = original_exception_count - len(rejected_ids)
    
    # Calculate updated match rate
    if original_exception_count > 0:
        updated_match_rate = ((original_exception_count - remaining_exception_count) / original_exception_count) * 100
        updated_match_rate = result['match_pct'] + (100 - result['match_pct']) * (len(rejected_ids) / original_exception_count)
    else:
        updated_match_rate = result['match_pct']
    
    with col1:
        st.metric(
            "Match Rate", 
            f"{updated_match_rate:.1f}%",
            delta=f"+{updated_match_rate - result['match_pct']:.1f}%" if len(rejected_ids) > 0 else None
        )
    with col2:
        st.metric(
            "Active Exceptions", 
            remaining_exception_count,
            delta=f"-{len(rejected_ids)}" if len(rejected_ids) > 0 else None
        )
    with col3:
        pk_display = ", ".join(map(str, result.get("primary_key", [])))
        st.metric("Primary Key(s)", pk_display)
    
    if result.get("exceptions"):
        st.subheader("🔍 Exception Management")
        
        # Show status overview
        original_total = len(result.get("exceptions", []))
        if rejected_ids:
            st.info(f"📊 **Status**: {len(rejected_ids)} exceptions rejected, {original_total - len(rejected_ids)} remaining active")
        else:
            st.info(f"📊 **Status**: {original_total} active exceptions (none rejected yet)")
        
        # Create exceptions dataframe
        exceptions_df = pd.DataFrame(result['exceptions'])
        
        # Filter out rejected exceptions AND RESET INDEX
        if rejected_ids:
            # Filter out rejected exceptions
            exceptions_df = exceptions_df[~exceptions_df.index.isin(rejected_ids)]
            # CRITICAL FIX: Reset index to create sequential [0,1,2,3...] indices
            exceptions_df = exceptions_df.reset_index(drop=True)
        
        if len(exceptions_df) > 0:
            # ADD SUMMARY COLUMN ON-THE-FLY
            exceptions_df['summary'] = exceptions_df.apply(
                lambda row: _build_summary_local(row['old'], row['new']), 
                axis=1
            )
            
            # Add rejection checkbox column
            exceptions_df['Reject Exception'] = False
            
            # Add helpful instructions
            st.markdown("""
            **💡 Instructions:**
            1. Review each exception below
            2. Check the "Reject Exception" box for differences you consider acceptable
            3. Click "Apply Rejections" to remove them and improve your match rate
            4. Rejected exceptions will be permanently hidden from future views
            """)
            st.markdown("---")
            
            # Get primary key columns and create dynamic column order
            pk_columns = result.get("primary_key", [])
            
            # Start with primary key columns, then add field, old, new, summary, reject
            column_order = pk_columns.copy()
            for col in ['field', 'old', 'new', 'summary']:
                if col in exceptions_df.columns and col not in column_order:
                    column_order.append(col)
            
            # Add rejection column at the end
            column_order.append('Reject Exception')
            
            # Add any remaining columns
            for col in exceptions_df.columns:
                if col not in column_order:
                    column_order.append(col)
            
            # Filter to only include columns that actually exist
            columns_to_show = [col for col in column_order if col in exceptions_df.columns]
            
            # Display editable dataframe
            edited_df = st.data_editor(
                exceptions_df[columns_to_show],
                column_config={
                    "field": st.column_config.TextColumn("Field Name"),
                    "old": st.column_config.TextColumn("Old Value"),
                    "new": st.column_config.TextColumn("New Value"),
                    "summary": st.column_config.TextColumn("Summary"),
                    "Reject Exception": st.column_config.CheckboxColumn(
                        "Reject Exception",
                        help="Mark this exception as acceptable (will be removed)",
                        default=False,
                    ),
                },
                disabled=["field", "old", "new", "summary"] + pk_columns,
                use_container_width=True,
                height=400,
                key=f"exceptions_editor_{system_name}"
            )
            
            # Add refresh button with enhanced styling
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                apply_button = st.button(
                    "🔄 Apply Rejections", 
                    key=f"apply_rejections_{system_name}",
                    help="Remove selected exceptions and update match rate",
                    type="primary"
                )
                
            if apply_button:
                # Get rejected exception IDs
                rejected_mask = edited_df['Reject Exception'] == True
                rejected_exception_ids = edited_df[rejected_mask].index.tolist()
                
                if rejected_exception_ids and analysis_id:
                    with st.spinner("Processing exception rejections..."):
                        # Send rejections to backend
                        result_api = reject_exceptions(system_name, analysis_id, rejected_exception_ids)
                        
                        if "error" not in result_api:
                            st.success(f"✅ Successfully rejected {len(rejected_exception_ids)} exceptions!")
                            
                            # Recalculate match rate and show improvement
                            match_result = recalculate_match_rate(analysis_id)
                            if "error" not in match_result:
                                new_rate = match_result.get('new_match_rate', result['match_pct'])
                                old_rate = match_result.get('old_match_rate', result['match_pct'])
                                improvement = new_rate - old_rate
                                
                                if improvement > 0:
                                    st.balloons()  # Celebrate improvement!
                                    st.success(f"🎉 Match rate improved by {improvement:.1f}%! ({old_rate:.1f}% → {new_rate:.1f}%)")
                                else:
                                    st.info(f"📊 Match rate: {new_rate:.1f}%")
                            
                            st.rerun()  # Refresh the page
                        else:
                            st.error(f"❌ Error: {result_api['error']}")
                elif not analysis_id:
                    st.warning("⚠️ Cannot reject exceptions: Analysis ID not available")
                else:
                    st.info("ℹ️ No exceptions selected for rejection")
            
            # Show current stats with proper calculation
            original_total = len(result.get("exceptions", []))
            current_remaining = len(exceptions_df)  # After filtering and reset
            total_rejected = len(rejected_ids)
            
            if rejected_ids:
                st.info(f"""
                **Exception Management Summary:**
                - Original exceptions: {original_total}
                - Rejected exceptions: {total_rejected}
                - Remaining exceptions: {current_remaining}
                - Updated match rate: {updated_match_rate:.1f}%
                """)
            
            st.caption(f"🔑 Primary Key(s): {pk_display}")
        else:
            st.success("🎉 All exceptions have been rejected! Perfect match achieved.")
            if rejected_ids:
                st.info(f"💡 {len(rejected_ids)} exceptions were marked as acceptable differences.")
    else:
        st.success("🎉 No exceptions found - Perfect match!")


def _build_summary_local(old_value, new_value):
    """Build summary locally in frontend - simple version."""
    try:
        # Handle null values
        if pd.isna(old_value) and pd.isna(new_value):
            return "no change"
        elif pd.isna(old_value):
            return f"added: {new_value}"
        elif pd.isna(new_value):
            return f"removed: {old_value}"
        
        # Try numeric comparison first
        try:
            old_v, new_v = float(old_value), float(new_value)
            delta = new_v - old_v
            if old_v != 0:
                pct = (delta / old_v * 100)
                return f"changed by {delta:+.2f} ({pct:+.2f}%)"
            else:
                return f"changed by {delta:+.2f}"
        except (ValueError, TypeError):
            pass
        
        # Try date comparison
        try:
            from dateutil import parser
            d_old = parser.parse(str(old_value))
            d_new = parser.parse(str(new_value))
            days = (d_new - d_old).days
            if days == 0:
                return "same date, time changed"
            else:
                return f"shifted by {days:+d} days"
        except:
            pass
        
        # Default to text comparison
        old_str, new_str = str(old_value), str(new_value)
        if len(old_str) > 30:
            old_str = old_str[:30] + "..."
        if len(new_str) > 30:
            new_str = new_str[:30] + "..."
        return f"from '{old_str}' to '{new_str}'"
        
    except Exception:
        return f"from {old_value} to {new_value}"