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
