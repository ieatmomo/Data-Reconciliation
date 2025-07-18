import pandas as pd
from sqlalchemy import create_engine
from typing import Dict, Any

def load_file(path: str) -> pd.DataFrame:
    """
    Read a CSV or Excel file into a pandas DataFrame.
    """
    if path.endswith('.csv'):
        return pd.read_csv(path)
    elif path.endswith(('.xls', '.xlsx')):
        return pd.read_excel(path)
    else:
        raise ValueError(f"Unsupported file type: {path}")

def normalize(df: pd.DataFrame, cfg: Dict[str, Any]) -> pd.DataFrame:
    """
    Clean and standardize a DataFrame according to the mapping config:
    - Lowercase & snake_case column names
    - Apply any explicit renames from cfg['fields'][*]['rename_to']
    - Perform string cleaning (strip, lowercase) per cfg['fields'][*]['clean']
    """
    # 1) Lowercase & snake-case all column names
    df = df.rename(columns={
        c: c.strip().lower().replace(' ', '_') for c in df.columns
    })

    # 2) Apply explicit renames from mapping config
    rename_map = {
        field: rules['rename_to']
        for field, rules in cfg.get('fields', {}).items()
        if 'rename_to' in rules
    }
    if rename_map:
        df = df.rename(columns=rename_map)

    # 3) Apply string cleaning rules
    for field, rules in cfg.get('fields', {}).items():
        if rules.get('type') == 'string' and 'clean' in rules and field in df.columns:
            for step in rules['clean']:
                if step == 'strip_whitespace':
                    df[field] = df[field].astype(str).str.strip()
                elif step == 'lowercase':
                    df[field] = df[field].astype(str).str.lower()

    # 4) (Optional) Add date parsing or other transforms here

    return df

def to_postgres(df: pd.DataFrame, table_name: str, engine_url: str):
    """
    Write a DataFrame into Postgres via SQLAlchemy.
    """
    engine = create_engine(engine_url)
    df.to_sql(table_name, engine, if_exists='replace', index=False)
