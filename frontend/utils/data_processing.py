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