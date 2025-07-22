import streamlit as st
import pandas as pd
from utils.api_client import get_available_systems, get_system_details, get_historical_data
from components.charts import display_historical_charts
from utils.data_processing import clean_system_name

def render_historical_browser():
    """Render the historical data browser section."""
    
    # =============================================================================
    # HISTORICAL DATA BROWSER SECTION
    # =============================================================================

    st.header("📈 Historical Data Browser")
    st.markdown("Browse historical reconciliation data for any system in the database.")

    # Load available systems (returns cleaned names)
    available_systems = _load_available_systems()

    if available_systems:
        # System selection using cleaned names
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_system_clean = st.selectbox(
                "Select System:",
                options=[""] + available_systems,  # These are already cleaned
                index=0,
                help="Choose a system to view its historical reconciliation data"
            )
        
        with col2:
            if selected_system_clean:
                # Get original system name for API calls
                system_mapping = st.session_state.get('system_mapping', {})
                selected_system_original = system_mapping.get(selected_system_clean, selected_system_clean)
                
                # Get system details using original name
                try:
                    system_details = get_system_details(selected_system_original)
                    if system_details:
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
        if selected_system_clean:
            # Display charts using cleaned name
            display_historical_charts(selected_system_clean, selected_pk)
            
            # Show historical exception records using CLEANED name for subtitle
            st.subheader(f"📋 Exception Records for {selected_system_clean.title()}")
            
            try:
                # Get original system name for API call
                system_mapping = st.session_state.get('system_mapping', {})
                selected_system_original = system_mapping.get(selected_system_clean, selected_system_clean)
                
                # Get historical data using original name
                graph_data = get_historical_data(selected_system_original, selected_pk)
                
                if graph_data and graph_data.get('dates'):
                    # Convert dates to datetime objects for filtering
                    dates_list = [pd.to_datetime(date) for date in graph_data['dates']]
                    min_date = min(dates_list).date()
                    max_date = max(dates_list).date()
                    
                    # Add date range selector
                    st.markdown("**📅 Filter by Date Range:**")
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        start_date = st.date_input(
                            "Start Date",
                            value=min_date,
                            min_value=min_date,
                            max_value=max_date,
                            key=f"start_date_{selected_system_clean}"
                        )
                    
                    with col2:
                        end_date = st.date_input(
                            "End Date", 
                            value=max_date,
                            min_value=min_date,
                            max_value=max_date,
                            key=f"end_date_{selected_system_clean}"
                        )
                    
                    # Add a helpful note instead of reset button
                    st.caption("💡 Tip: Use the date pickers above to adjust the range. Default shows all available data.")
                    
                    # Validate date range
                    if start_date > end_date:
                        st.error("Start date cannot be after end date!")
                        st.stop()
                    
                    # Filter data based on date range
                    filtered_data = []
                    for i, date_str in enumerate(graph_data['dates']):
                        date_obj = pd.to_datetime(date_str).date()
                        if start_date <= date_obj <= end_date:
                            # Get primary key for this specific run
                            pk_used = graph_data.get('primary_keys_used', [None] * len(graph_data['dates']))[i]
                            if not pk_used:
                                pk_used = selected_pk if selected_pk else "Auto-detected"
                            
                            filtered_data.append({
                                'Date': date_str,
                                'Primary Key': pk_used,
                                'Match Rate (%)': graph_data['match_rates'][i],
                                'Exception Count': graph_data['exception_counts'][i],
                                'Status': '✅ Good' if graph_data['match_rates'][i] >= 95 else '⚠️ Check Required' if graph_data['match_rates'][i] >= 90 else '❌ Issues'
                            })
                    
                    if filtered_data:
                        summary_df = pd.DataFrame(filtered_data)
                        
                        # Show filtered results summary
                        st.info(f"📊 Showing {len(filtered_data)} records from {start_date} to {end_date}")
                        
                        # Display the summary table
                        st.dataframe(
                            summary_df,
                            height=300,
                            use_container_width=True,
                            column_config={
                                "Date": st.column_config.DateColumn("Date"),
                                "Primary Key": st.column_config.TextColumn("Primary Key"),
                                "Match Rate (%)": st.column_config.NumberColumn("Match Rate (%)", format="%.1f"),
                                "Exception Count": st.column_config.NumberColumn("Exception Count"),
                                "Status": st.column_config.TextColumn("Status")
                            }
                        )
                        
                        # Show filtered summary stats
                        if len(filtered_data) > 0:
                            avg_match_rate = sum([row['Match Rate (%)'] for row in filtered_data]) / len(filtered_data)
                            total_exceptions = sum([row['Exception Count'] for row in filtered_data])
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Records", len(filtered_data))
                            with col2:
                                st.metric("Avg Match Rate", f"{avg_match_rate:.1f}%")
                            with col3:
                                st.metric("Total Exceptions", total_exceptions)
                            with col4:
                                good_records = len([r for r in filtered_data if r['Match Rate (%)'] >= 95])
                                st.metric("Good Runs", f"{good_records}/{len(filtered_data)}")
                        
                        # Download option using CLEANED name and date range in filename
                        csv_data = summary_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Filtered Data as CSV",
                            data=csv_data,
                            file_name=f"historical_data_{selected_system_clean}_{start_date}_{end_date}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.warning(f"No data found for the selected date range: {start_date} to {end_date}")
                        
                else:
                    st.info(f"No historical data found for system: {selected_system_clean}")
                    
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
    st.session_state['system_mapping'] = system_mapping
    
    return sorted(list(cleaned_systems))