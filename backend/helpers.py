import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET
from collections import Counter

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
    """
    Convert pandas/numpy types to JSON-serializable types.
    """
    if isinstance(obj, dict):
        return {k: convert_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_json_safe(v) for v in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif pd.isna(obj):
        return None
    else:
        return obj

def parse_uploaded_file(file_path: str, filename: str) -> pd.DataFrame:
    """
    Parse uploaded files of different types (CSV, Excel, XML).
    This handles all file parsing logic for the backend.
    """
    try:
        # Determine file type from extension
        if filename.lower().endswith('.csv'):
            return parse_csv_file(file_path)
        elif filename.lower().endswith(('.xls', '.xlsx')):
            return parse_excel_file(file_path)
        elif filename.lower().endswith('.xml'):
            return parse_xml_file(file_path)
        else:
            raise ValueError(f"Unsupported file type: {filename}")
    except Exception as e:
        raise Exception(f"Failed to parse {filename}: {str(e)}")

def parse_csv_file(file_path: str) -> pd.DataFrame:
    """
    Parse CSV files with encoding detection and error handling.
    """
    try:
        return pd.read_csv(file_path)
    except UnicodeDecodeError:
        # Try different encodings if UTF-8 fails
        try:
            return pd.read_csv(file_path, encoding='latin-1')
        except UnicodeDecodeError:
            return pd.read_csv(file_path, encoding='utf-8-sig')
    except Exception as e:
        raise Exception(f"Failed to parse CSV file: {str(e)}")

def parse_excel_file(file_path: str) -> pd.DataFrame:
    """
    Parse Excel files with different engine fallbacks.
    """
    try:
        return pd.read_excel(file_path, engine='openpyxl')
    except Exception:
        try:
            # Try with different engine for older Excel files
            return pd.read_excel(file_path, engine='xlrd')
        except Exception as e:
            raise Exception(f"Failed to parse Excel file: {str(e)}")

def parse_xml_file(file_path: str) -> pd.DataFrame:
    """
    Parse XML files - simplified version for your products structure.
    """
    try:
        # Try pandas first (this should work for your XML)
        df = pd.read_xml(file_path)
        print(f"Successfully parsed XML with pandas, shape: {df.shape}")
        return df
    except Exception as pandas_error:
        print(f"Pandas failed: {pandas_error}")
        try:
            # Manual parsing as fallback
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            records = []
            for product in root.findall('product'):
                record = {}
                for field in product:
                    record[field.tag] = field.text
                records.append(record)
            
            df = pd.DataFrame(records)
            print(f"Successfully parsed XML manually, shape: {df.shape}")
            return df
            
        except Exception as manual_error:
            raise Exception(f"Both parsing methods failed. Pandas: {pandas_error}, Manual: {manual_error}")

def get_file_columns_preview(file_path: str, filename: str, max_rows: int = 5) -> dict:
    """
    Get a preview of file columns and sample data for large files.
    """
    try:
        if filename.lower().endswith('.csv'):
            df_preview = pd.read_csv(file_path, nrows=max_rows)
        elif filename.lower().endswith(('.xls', '.xlsx')):
            df_preview = pd.read_excel(file_path, nrows=max_rows)
        elif filename.lower().endswith('.xml'):
            df_preview = parse_xml_preview(file_path, max_rows)
        else:
            raise ValueError(f"Unsupported file type: {filename}")
        
        return {
            "columns": df_preview.columns.tolist(),
            "sample_data": df_preview.to_dict('records'),
            "row_count": len(df_preview)
        }
    except Exception as e:
        return {
            "error": f"Failed to preview {filename}: {str(e)}",
            "columns": [],
            "sample_data": [],
            "row_count": 0
        }

def parse_xml_preview(file_path: str, max_rows: int = 5) -> pd.DataFrame:
    """
    Parse only the first few XML records for performance.
    """
    try:
        return pd.read_xml(file_path, nrows=max_rows)
    except:
        tree = ET.parse(file_path)
        root = tree.getroot()
        tags = [child.tag for child in root]
        most_common_tag = Counter(tags).most_common(1)[0][0]
        
        rows = []
        for i, record in enumerate(root.findall(most_common_tag)):
            if i >= max_rows:
                break
            row = {c.tag: c.text for c in record}
            rows.append(row)
        
        return pd.DataFrame(rows)

def detect_file_encoding(file_path: str) -> str:
    """
    Detect file encoding using simple heuristics.
    """
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(1024)  # Read first 1KB
            
        try:
            raw_data.decode('utf-8')
            return 'utf-8'
        except UnicodeDecodeError:
            try:
                raw_data.decode('latin-1')
                return 'latin-1'
            except UnicodeDecodeError:
                return 'utf-8-sig'  # UTF-8 with BOM
    except Exception:
        return 'utf-8'  # Default fallback

def optimize_dataframe_memory(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize DataFrame memory usage for large files.
    """
    # Convert object columns to category where appropriate
    for col in df.columns:
        if df[col].dtype == 'object':
            if df[col].nunique() / len(df) < 0.5:  # If less than 50% unique values
                df[col] = df[col].astype('category')
    
    # Downcast numeric types
    for col in df.select_dtypes(include=['int']).columns:
        df[col] = pd.to_numeric(df[col], downcast='integer')
    
    for col in df.select_dtypes(include=['float']).columns:
        df[col] = pd.to_numeric(df[col], downcast='float')
    
    return df

def validate_file_structure(df: pd.DataFrame, min_rows: int = 1, min_cols: int = 1) -> dict:
    """
    Validate file structure and return validation results.
    """
    validation_result = {
        "is_valid": True,
        "warnings": [],
        "errors": []
    }
    
    # Check minimum requirements
    if len(df) < min_rows:
        validation_result["errors"].append(f"File has {len(df)} rows, minimum required: {min_rows}")
        validation_result["is_valid"] = False
    
    if len(df.columns) < min_cols:
        validation_result["errors"].append(f"File has {len(df.columns)} columns, minimum required: {min_cols}")
        validation_result["is_valid"] = False
    
    # Check for empty columns
    empty_cols = df.columns[df.isnull().all()].tolist()
    if empty_cols:
        validation_result["warnings"].append(f"Empty columns detected: {empty_cols}")
    
    # Check for duplicate column names
    duplicate_cols = df.columns[df.columns.duplicated()].tolist()
    if duplicate_cols:
        validation_result["errors"].append(f"Duplicate column names detected: {duplicate_cols}")
        validation_result["is_valid"] = False
    
    return validation_result

