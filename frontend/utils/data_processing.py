import pandas as pd

def clean_system_name(system_name):
    """
    Clean system name by extracting the base name (0th index after splitting).
    Used consistently throughout the app for display purposes.
    """
    if not system_name:
        return system_name
    
    # Split by common delimiters and take the first part
    delimiters = ['_', '-', ' ']
    clean_name = system_name.lower().strip()
    
    for delimiter in delimiters:
        if delimiter in clean_name:
            clean_name = clean_name.split(delimiter)[0]
            break
    
    return clean_name

def build_summary_local(old_value, new_value):
    """Build summary locally in frontend - reusable function."""
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