import pandas as pd
from dateutil import parser

def add_summary_to_exceptions(exceptions, config=None):
    """
    Add summary column to existing exception records.
    
    Args:
        exceptions (list): List of exception dictionaries
        config (dict): Optional configuration for field types
    
    Returns:
        list: Exception records with summary column added
    """
    if not exceptions:
        return exceptions
    
    # Add summary to each exception
    for exc in exceptions:
        field_name = exc.get('field')
        old_value = exc.get('old')
        new_value = exc.get('new')
        
        # Get field type from config if available
        field_type = None
        if config and field_name:
            field_config = config.get('fields', {}).get(field_name, {})
            field_type = field_config.get('type')
        
        # Build and add summary
        exc['summary'] = build_summary(old_value, new_value, field_type)
    
    return exceptions

def build_summary(old_value, new_value, field_type=None):
    """
    Build a summary description of the change between old and new values.
    """
    try:
        o, n = old_value, new_value
        
        # Handle null values
        if pd.isna(o) and pd.isna(n):
            return "no change"
        elif pd.isna(o):
            return f"added: {n}"
        elif pd.isna(n):
            return f"removed: {o}"
        
        # Handle numeric/decimal fields
        if field_type in ("numeric", "integer", "decimal"):
            return _build_numeric_summary(o, n)
        
        # Handle date fields
        elif field_type == "date":
            return _build_date_summary(o, n)
        
        # Default for strings and other types
        else:
            return _build_text_summary(o, n)
            
    except Exception as e:
        print(f"Error building summary: {e}")
        return f"from {old_value} to {new_value}"

def _build_numeric_summary(old_value, new_value):
    """Build summary for numeric fields with delta and percentage."""
    try:
        old_v, new_v = float(old_value), float(new_value)
        delta = new_v - old_v
        
        if old_v != 0:
            pct = (delta / old_v * 100)
            return f"changed by {delta:+.2f} ({pct:+.2f}%)"
        else:
            return f"changed by {delta:+.2f}"
            
    except (ValueError, TypeError):
        return f"from {old_value} to {new_value}"

def _build_date_summary(old_value, new_value):
    """Build summary for date fields showing day difference."""
    try:
        d_old = parser.parse(str(old_value))
        d_new = parser.parse(str(new_value))
        days = (d_new - d_old).days
        
        if days == 0:
            return "same date, time changed"
        elif days == 1:
            return "shifted by 1 day"
        elif days == -1:
            return "shifted by -1 day"
        else:
            return f"shifted by {days:+d} days"
            
    except Exception:
        return f"from {old_value} to {new_value}"

def _build_text_summary(old_value, new_value):
    """Build summary for text fields with smart truncation."""
    old_str = str(old_value)
    new_str = str(new_value)
    
    # Truncate long strings for readability
    max_length = 30
    
    if len(old_str) > max_length:
        old_display = old_str[:max_length] + "..."
    else:
        old_display = old_str
        
    if len(new_str) > max_length:
        new_display = new_str[:max_length] + "..."
    else:
        new_display = new_str
    
    return f"from '{old_display}' to '{new_display}'"