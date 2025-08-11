import streamlit as st
import pandas as pd
from utils.api_client import get_available_systems, get_system_details, get_historical_data, get_specific_analysis, reject_exceptions, get_rejected_exceptions, recalculate_match_rate
from utils.data_processing import clean_system_name

def render_previous_analysis():
    """Render the previous analysis viewer section."""
    
    st.header("🔍 View Previous Analysis")
    st.markdown("Select a specific analysis to view the detailed exception records.")
    
    # Load available systems
    available_systems = _load_available_systems()
    
    if not available_systems:
        _show_no_data_message()
        return
    
    # System selection
    selected_system_clean, selected_pk, selected_date = _render_analysis_selection(available_systems)
    
    if selected_system_clean and selected_date:
        _display_analysis_results(selected_system_clean, selected_pk, selected_date)

def _load_available_systems():
    """Load available systems from the database and return cleaned names."""
    raw_systems = get_available_systems()
    if not raw_systems:
        return []
    
    # Create mapping of cleaned names to original names
    system_mapping = {}
    cleaned_systems = set()
    
    for system in raw_systems:
        clean_name = clean_system_name(system)
        if clean_name:
            cleaned_systems.add(clean_name)
            # Store first original name for each clean name
            if clean_name not in system_mapping:
                system_mapping[clean_name] = system
    
    # Store mapping in session state for API calls
    st.session_state['prev_analysis_system_mapping'] = system_mapping
    
    return sorted(list(cleaned_systems))

def _render_analysis_selection(available_systems):
    """Render system, primary key, and date selection widgets."""
    
    col1, col2, col3 = st.columns([2, 2, 2])
    
    # System selection
    with col1:
        selected_system_clean = st.selectbox(
            "Select System:",
            options=[""] + available_systems,
            index=0,
            help="Choose a system to view previous analysis",
            key="prev_analysis_system"
        )
    
    selected_pk = None
    selected_date = None
    
    # Primary key selection
    with col2:
        if selected_system_clean:
            selected_pk = _render_primary_key_filter(selected_system_clean)
    
    # Date selection
    with col3:
        if selected_system_clean:
            selected_date = _render_date_selection(selected_system_clean, selected_pk)
    
    return selected_system_clean, selected_pk, selected_date

def _render_primary_key_filter(selected_system_clean):
    """Render primary key filter for selected system."""
    system_mapping = st.session_state.get('prev_analysis_system_mapping', {})
    selected_system_original = system_mapping.get(selected_system_clean, selected_system_clean)
    
    try:
        system_details = get_system_details(selected_system_original)
        if system_details:
            available_pks = system_details.get("primary_keys", [])
            
            if len(available_pks) > 1:
                selected_pk = st.selectbox(
                    "Primary Key:",
                    options=["All"] + available_pks,
                    help="Select specific primary key combination",
                    key="prev_analysis_pk"
                )
                return None if selected_pk == "All" else selected_pk
            elif available_pks:
                st.info(f"PK: {available_pks[0]}")
                return available_pks[0]
        
        return None
        
    except Exception as e:
        st.error(f"Error loading system details: {e}")
        return None

def _render_date_selection(selected_system_clean, selected_pk):
    """Render date selection dropdown with available analysis dates."""
    system_mapping = st.session_state.get('prev_analysis_system_mapping', {})
    selected_system_original = system_mapping.get(selected_system_clean, selected_system_clean)
    
    try:
        # Get historical data to populate available dates
        graph_data = get_historical_data(selected_system_original, selected_pk)
        
        if graph_data and graph_data.get('dates'):
            # Create options with date and match rate for better context
            date_options = []
            for i, date in enumerate(graph_data['dates']):
                match_rate = graph_data['match_rates'][i]
                exception_count = graph_data['exception_counts'][i]
                date_options.append({
                    'date': date,
                    'display': f"{date} (Match: {match_rate:.1f}%, Exceptions: {exception_count})",
                    'match_rate': match_rate,
                    'exception_count': exception_count
                })
            
            # Sort by date descending (most recent first)
            date_options.sort(key=lambda x: x['date'], reverse=True)
            
            # Create selectbox with enhanced display
            display_options = [""] + [opt['display'] for opt in date_options]
            
            selected_display = st.selectbox(
                "Analysis Date:",
                options=display_options,
                help="Select a specific analysis date to view detailed exceptions",
                key="prev_analysis_date"
            )
            
            if selected_display and selected_display != "":
                # Find the actual date from the display string
                selected_date = next(
                    (opt['date'] for opt in date_options if opt['display'] == selected_display),
                    None
                )
                return selected_date
        else:
            st.info("No analysis dates available for this system/PK combination")
        
        return None
        
    except Exception as e:
        st.error(f"Error loading analysis dates: {e}")
        return None

def _display_analysis_results(selected_system_clean, selected_pk, selected_date):
    """Display the exception results for the selected analysis."""
    
    system_mapping = st.session_state.get('prev_analysis_system_mapping', {})
    selected_system_original = system_mapping.get(selected_system_clean, selected_system_clean)
    
    st.subheader(f"📋 Analysis Results for {selected_system_clean.title()}")
    st.info(f"🗓️ Date: {selected_date} | 🔑 Primary Key: {selected_pk or 'All'}")
    
    try:
        # Get the specific analysis data
        analysis_data = get_specific_analysis(selected_system_original, selected_pk, selected_date)
        
        if not analysis_data:
            st.warning("No detailed exception data found for this analysis.")
            st.markdown("""
            **Possible reasons:**
            - This analysis had no exceptions (100% match rate)
            - Detailed exception data is not available for this date
            - The analysis was performed before detailed logging was implemented
            """)
            return
        
        # Display analysis summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Match Rate", f"{analysis_data.get('match_rate', 0):.1f}%")
        with col2:
            exception_count = len(analysis_data.get('exceptions', []))
            st.metric("Exception Count", exception_count)
        with col3:
            pk_display = analysis_data.get('primary_key_used', 'Unknown')
            st.metric("Primary Key Used", pk_display)
        
        # Display exceptions table
        exceptions = analysis_data.get('exceptions', [])
        if exceptions:
            # Pass all required parameters including selected_system_clean and selected_date
            _render_exceptions_table(
                exceptions, 
                analysis_data.get('primary_key_used', '').split(','),
                selected_system_clean,
                selected_date
            )
        else:
            st.success("🎉 No exceptions found - Perfect match!")
            
    except Exception as e:
        st.error(f"Error loading analysis results: {e}")

def _render_exceptions_table(exceptions, pk_columns, selected_system_clean, selected_date):
    """Render the exceptions data table with exception management."""
    
    exceptions_df = pd.DataFrame(exceptions)
    
    if exceptions_df.empty:
        st.info("No exceptions to display.")
        return
    
    # Get system mapping for API calls
    system_mapping = st.session_state.get('prev_analysis_system_mapping', {})
    selected_system_original = system_mapping.get(selected_system_clean, selected_system_clean)
    
    # Get analysis data to extract analysis_id
    analysis_data = get_specific_analysis(selected_system_original, None, selected_date)
    analysis_id = analysis_data.get('analysis_id') if analysis_data else None
    
    # Get rejected exceptions if analysis_id is available
    rejected_ids = []
    if analysis_id:
        rejected_response = get_rejected_exceptions(selected_system_original, analysis_id)
        rejected_ids = rejected_response.get("rejected_ids", [])
    
    # Filter out rejected exceptions AND RESET INDEX
    if rejected_ids:
        # Filter out rejected exceptions
        exceptions_df = exceptions_df[~exceptions_df.index.isin(rejected_ids)]
        # CRITICAL FIX: Reset index to create sequential [0,1,2,3...] indices
        exceptions_df = exceptions_df.reset_index(drop=True)
    
    if len(exceptions_df) > 0:
        # ADD SUMMARY COLUMN ON-THE-FLY (same as above)
        exceptions_df['summary'] = exceptions_df.apply(
            lambda row: _build_summary_local(row['old'], row['new']), 
            axis=1
        )
        
        # Add rejection checkbox column
        exceptions_df['Reject Exception'] = False
        
        # Clean up primary key columns (remove any empty strings)
        pk_columns = [pk.strip() for pk in pk_columns if pk.strip()]
        
        # Create dynamic column order: PKs first, then field, old, new, summary, reject
        column_order = pk_columns.copy() if pk_columns else []
        
        # Add standard exception columns INCLUDING summary and rejection
        for col in ['field', 'old', 'new', 'summary']:
            if col in exceptions_df.columns and col not in column_order:
                column_order.append(col)
        
        # Add rejection column
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
            key=f"prev_exceptions_editor_{selected_system_clean}_{selected_date}"
        )
        
        # Add refresh button with enhanced styling
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            apply_button = st.button(
                "🔄 Apply Rejections", 
                key=f"prev_apply_rejections_{selected_system_clean}_{selected_date}",
                help="Remove selected exceptions and update analysis",
                type="primary"
            )
            
        if apply_button:
            # Get rejected exception IDs
            rejected_mask = edited_df['Reject Exception'] == True
            rejected_exception_ids = edited_df[rejected_mask].index.tolist()
            
            if rejected_exception_ids and analysis_id:
                with st.spinner("Processing exception rejections..."):
                    # Send rejections to backend
                    result_api = reject_exceptions(selected_system_original, analysis_id, rejected_exception_ids)
                    
                    if "error" not in result_api:
                        st.success(f"✅ Successfully rejected {len(rejected_exception_ids)} exceptions!")
                        
                        # Recalculate match rate and show improvement
                        match_result = recalculate_match_rate(analysis_id)
                        if "error" not in match_result:
                            new_rate = match_result.get('new_match_rate')
                            old_rate = match_result.get('old_match_rate')
                            
                            if new_rate and old_rate:
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
        original_total = len(exceptions) if exceptions else 0
        current_remaining = len(exceptions_df)  # After filtering and reset
        total_rejected = len(rejected_ids)
        
        if rejected_ids:
            st.info(f"""
            **Exception Management Summary:**
            - Original exceptions: {original_total}
            - Rejected exceptions: {total_rejected}
            - Remaining exceptions: {current_remaining}
            """)
        
        # Show summary info
        st.caption(f"🔑 Primary Key(s): {', '.join(pk_columns) if pk_columns else 'Unknown'}")
        
        # Add download button for exceptions
        csv_data = exceptions_df[columns_to_show].to_csv(index=False)
        st.download_button(
            label="📥 Download Exceptions as CSV",
            data=csv_data,
            file_name=f"exceptions_{selected_system_clean}_{selected_date}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.success("🎉 All exceptions have been rejected! Perfect match achieved.")
        if rejected_ids:
            st.info(f"💡 {len(rejected_ids)} exceptions were marked as acceptable differences.")

def _build_summary_local(old_value, new_value):
    """Build summary locally in frontend - same function as file_upload.py"""
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

def _show_no_data_message():
    """Show message when no data is available."""
    st.info("🔍 No analysis data found in the database.")
    st.markdown("""
    **To get started:**
    1. Upload and analyze some files using the File Upload section
    2. Return here to view previous analysis results
    """)