import pandas as pd
import yaml
from typing import Dict, Any, List

def detect_primary_key(df_old: pd.DataFrame, df_new: pd.DataFrame) -> List[str]:
    """
    Automatically determine primary key column(s) by identifying fields
    that are unique and present in both datasets. If no single unique column exists,
    fallback to the top two columns with highest uniqueness.
    """
    # Find common columns
    common_cols = [col for col in df_old.columns if col in df_new.columns]
    # Identify truly unique columns
    unique_cols = [
        col for col in common_cols
        if df_old[col].is_unique and df_new[col].is_unique
    ]
    if unique_cols:
        # Return the first fully unique column
        return [unique_cols[0]]
    # Fallback: score columns by number of distinct values
    uniqueness_scores = {col: df_old[col].nunique() for col in common_cols}
    sorted_cols = sorted(uniqueness_scores, key=uniqueness_scores.get, reverse=True)
    # Return top two candidates for a composite key
    return sorted_cols[:2]

def load_mapping(path: str) -> Dict[str, Any]:
    """
    Load the reconciliation mapping config from a YAML file.
    Returns a dict with keys: pair_name (str), pk (List[str]), fields (dict).
    """
    with open(path, 'r') as f:
        cfg = yaml.safe_load(f)
    # Normalize the pair name
    if 'pair_name' in cfg:
        cfg['pair_name'] = str(cfg['pair_name']).strip().lower()
    # Normalize primary key list
    cfg['pk'] = [str(k).strip().lower() for k in cfg.get('pk', [])]
    # Normalize field configs
    fields_cfg = {}
    for field, rules in cfg.get('fields', {}).items():
        key = str(field).strip().lower()
        fields_cfg[key] = rules or {}
    cfg['fields'] = fields_cfg
    return cfg
