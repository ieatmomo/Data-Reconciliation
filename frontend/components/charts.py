import streamlit as st
import plotly.graph_objects as go
from utils.api_client import get_historical_data

def display_historical_charts(selected_system_clean, selected_pk=None):
    """Display historical charts for the selected system using cleaned names for display."""
    if not selected_system_clean:
        return
    
    # Get original system name for API calls
    system_mapping = st.session_state.get('system_mapping', {})
    selected_system_original = system_mapping.get(selected_system_clean, selected_system_clean)
    
    # Get historical data using original system name
    graph_data = get_historical_data(selected_system_original, selected_pk)
    
    if graph_data and graph_data.get('dates'):
        # Create two separate charts using CLEANED name for titles
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
                title=f'Exception Count Trend - {selected_system_clean.title()}',  # CLEANED NAME
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
                title=f'Match Rate Trend - {selected_system_clean.title()}',  # CLEANED NAME
                xaxis=dict(title='Date', type='category'),
                yaxis=dict(title='Match Rate (%)', range=[0, 100]),
                height=400
            )
            st.plotly_chart(fig_match_rate, use_container_width=True)
            
        # Show summary stats using CLEANED name
        avg_match_rate = sum(graph_data['match_rates'])/len(graph_data['match_rates']) if graph_data['match_rates'] else 0
        total_exceptions = sum(graph_data['exception_counts']) if graph_data['exception_counts'] else 0
        
        st.markdown(f"""
        **📊 Summary for {selected_system_clean.title()}:**
        - **Total Runs**: {len(graph_data['dates'])}
        - **Average Match Rate**: {avg_match_rate:.1f}%
        - **Total Exceptions**: {total_exceptions}
        - **Date Range**: {graph_data['dates'][0]} to {graph_data['dates'][-1]}
        """)
    else:
        st.info(f"No historical data available for system: {selected_system_clean}")