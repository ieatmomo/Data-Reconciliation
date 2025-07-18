import numpy as np

def file_checker(file):
    '''
    Helper Function to check if uploaded files are of allowed types:
    CSV, XLSX, XLS, XML
    '''
    allowed_extensions = {'csv', 'xlsx', 'xls', 'xml'}
    filename = file.filename

    extension = filename.rsplit('.', 1)[1].lower()

    if extension in allowed_extensions:
        return True
    else:
        raise ValueError(f"Unsupported file type: {extension}. Allowed types are: {', '.join(allowed_extensions)}")
    
def convert_json_safe(obj):
    if isinstance(obj, dict):
        return {k: convert_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_json_safe(v) for v in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    else:
        return obj

