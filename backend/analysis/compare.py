import pandas as pd
from rapidfuzz import fuzz

def run_compare(df_old, df_new, pk_cols, cfg=None):
    """
    Compare df_old vs. df_new on the key(s) in pk_cols, applying cfg for tolerances/fuzzy rules.
    Returns a dict with match_pct and a list of exception dicts.
    """
    try:
        print(f"Starting comparison with PK columns: {pk_cols}")
        print(f"Old DF shape: {df_old.shape}, New DF shape: {df_new.shape}")
        
        # 1) Merge on the detected PK(s)
        merged = df_old.merge(
            df_new,
            on=pk_cols,
            suffixes=('_old', '_new'),
            how='outer',
            indicator=True
        )
        print(f"Merged DF shape: {merged.shape}")

        # 2) Determine which columns to compare (exclude PKs)
        compare_cols = [c for c in df_old.columns if c not in pk_cols]
        print(f"Columns to compare: {compare_cols}")

        # 3) Compute total possible comparisons
        total = len(merged) * len(compare_cols)
        print(f"Total comparisons: {total}")

        exceptions = []
        for col in compare_cols:
            old_col = f"{col}_old"
            new_col = f"{col}_new"
            rules = (cfg or {}).get('fields', {}).get(col, {})

            # Skip if explicitly ignored
            if rules.get('type') == 'ignore':
                continue

            print(f"Processing column: {col} with rules: {rules}")

            # String fuzzy match
            if rules.get('type') == 'string' and 'fuzzy_match' in rules:
                thresh = rules['fuzzy_match']
                for idx in merged.index:
                    try:
                        o = merged.loc[idx, old_col]
                        n = merged.loc[idx, new_col]
                        
                        # Handle null values properly
                        if pd.isna(o) and pd.isna(n):
                            continue  # Both null = match
                        elif pd.isna(o) or pd.isna(n):
                            # One null, one not = mismatch
                            pk_values = get_pk_values(merged, idx, pk_cols)
                            exceptions.append({
                                **pk_values,
                                "field": col,
                                "old": o,
                                "new": n,
                            })
                        elif fuzz.ratio(str(o), str(n)) < thresh:
                            pk_values = get_pk_values(merged, idx, pk_cols)
                            exceptions.append({
                                **pk_values,
                                "field": col,
                                "old": o,
                                "new": n,
                            })
                    except Exception as e:
                        print(f"Error processing fuzzy match for {col} at index {idx}: {e}")
                        continue

            # Decimal tolerance
            elif rules.get('type') == 'decimal' and 'tolerance' in rules:
                tol = rules['tolerance']
                for idx in merged.index:
                    try:
                        o = merged.loc[idx, old_col]
                        n = merged.loc[idx, new_col]
                        
                        # Handle null values properly
                        if pd.isna(o) and pd.isna(n):
                            continue  # Both null = match
                        elif pd.isna(o) or pd.isna(n):
                            # One null, one not = mismatch
                            pk_values = get_pk_values(merged, idx, pk_cols)
                            exceptions.append({
                                **pk_values,
                                "field": col,
                                "old": o,
                                "new": n,
                            })
                        else:
                            try:
                                if abs(float(o) - float(n)) > tol:
                                    pk_values = get_pk_values(merged, idx, pk_cols)
                                    exceptions.append({
                                        **pk_values,
                                        "field": col,
                                        "old": o,
                                        "new": n,
                                    })
                            except (ValueError, TypeError):
                                # Can't convert to float = mismatch
                                pk_values = get_pk_values(merged, idx, pk_cols)
                                exceptions.append({
                                    **pk_values,
                                    "field": col,
                                    "old": o,
                                    "new": n,
                                })
                    except Exception as e:
                        print(f"Error processing decimal comparison for {col} at index {idx}: {e}")
                        continue

            # Default exact compare
            else:
                try:
                    diff_mask = merged[old_col].fillna('__NA__') != merged[new_col].fillna('__NA__')
                    for idx in merged[diff_mask].index:
                        try:
                            pk_values = get_pk_values(merged, idx, pk_cols)
                            exceptions.append({
                                **pk_values,
                                "field": col,
                                "old": merged.loc[idx, old_col],
                                "new": merged.loc[idx, new_col],
                            })
                        except Exception as e:
                            print(f"Error creating exception for {col} at index {idx}: {e}")
                            continue
                except Exception as e:
                    print(f"Error in exact comparison for column {col}: {e}")
                    continue

        # 4) Calculate match percentage properly
        n_exceptions = len(exceptions)
        match_pct = round(100 * (total - n_exceptions) / total, 2) if total else 0.0
        
        print(f"Comparison completed. Exceptions: {n_exceptions}, Match %: {match_pct}")
        return {"match_pct": match_pct, "exceptions": exceptions}
        
    except Exception as e:
        print(f"Critical error in run_compare: {e}")
        import traceback
        traceback.print_exc()
        raise

def get_pk_values(merged_df, idx, pk_cols):
    """
    Safely extract primary key values from merged dataframe.
    """
    pk_values = {}
    for k in pk_cols:
        try:
            # Primary key columns should exist without suffix after merge
            if k in merged_df.columns:
                pk_values[k] = merged_df.loc[idx, k]
            else:
                # Fallback: try to find the column with suffix
                if f"{k}_old" in merged_df.columns:
                    pk_values[k] = merged_df.loc[idx, f"{k}_old"]
                elif f"{k}_new" in merged_df.columns:
                    pk_values[k] = merged_df.loc[idx, f"{k}_new"]
                else:
                    pk_values[k] = "Unknown"
        except Exception as e:
            print(f"Error getting PK value for {k}: {e}")
            pk_values[k] = "Error"
    
    return pk_values
