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