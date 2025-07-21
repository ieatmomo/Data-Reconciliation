'''
NOT NEEDED ANYMORE
'''

# import matplotlib.pyplot as plt
# import numpy as np

# def create_trend_graph(query_results):
#     #Create a bar chart with line graph overlay using the audit data within the DB
#     #x-axis: date
#     #y-axis: Exception count
#     #line: Match rate
#     #title: 'File system' match rate over time
    
#     dates = [result['date'] for result in query_results]
#     match_rates = [result['match_rate'] for result in query_results]
#     exception_counts = [result['num_exceptions'] for result in query_results]
    
#     fig, ax1 = plt.subplots(figsize=(12, 6))
    
#     # Create bar chart for exception counts
#     bars = ax1.bar(dates, exception_counts, alpha=0.7, color='lightcoral', label='Exception Count')
#     ax1.set_xlabel('Date')
#     ax1.set_ylabel('Number of Exceptions', color='red')
#     ax1.tick_params(axis='y', labelcolor='red')
    
#     # Create second y-axis for line graph
#     ax2 = ax1.twinx()
    
#     # Create line graph for match rates
#     line = ax2.plot(dates, match_rates, color='blue', marker='o', linewidth=2, 
#                     markersize=6, label='Match Rate %')
#     ax2.set_ylabel('Match Rate (%)', color='blue')
#     ax2.tick_params(axis='y', labelcolor='blue')
#     ax2.set_ylim(0, 100)  # Match rate is typically 0-100%
    
#     # Add value labels on top of bars
#     for bar, count in zip(bars, exception_counts):
#         height = bar.get_height()
#         ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
#                 f'{count}', ha='center', va='bottom', fontsize=10)
    
#     # Add value labels on line points
#     for i, (date, rate) in enumerate(zip(dates, match_rates)):
#         ax2.text(date, rate + 2, f'{rate:.1f}%', ha='center', va='bottom', 
#                 fontsize=10, color='blue')
    
#     # Formatting
#     plt.title('Reconciliation Trend: Exceptions vs Match Rate', fontsize=14, fontweight='bold')
#     plt.xticks(rotation=45)
#     plt.tight_layout()
    
#     # Add legends
#     ax1.legend(loc='upper left')
#     ax2.legend(loc='upper right')
    
#     return fig