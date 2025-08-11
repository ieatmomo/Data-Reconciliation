# import pandas as pd
# from rapidfuzz import fuzz

# def run_compare(df_old, df_new, pk_cols, cfg=None):
#     """
#     Compare df_old vs. df_new on the key(s) in pk_cols, applying cfg for tolerances/fuzzy rules.
#     Returns a dict with match_pct and a list of exception dicts.
#     """
#     try:
#         print(f"Starting comparison with PK columns: {pk_cols}")
#         print(f"Old DF shape: {df_old.shape}, New DF shape: {df_new.shape}")
        
#         # 1) Merge on the detected PK(s)
#         merged = df_old.merge(
#             df_new,
#             on=pk_cols,
#             suffixes=('_old', '_new'),
#             how='outer',
#             indicator=True
#         )
#         print(f"Merged DF shape: {merged.shape}")

#         # 2) Determine which columns to compare (exclude PKs)
#         compare_cols = [c for c in df_old.columns if c not in pk_cols]
#         print(f"Columns to compare: {compare_cols}")

#         # 3) Compute total possible comparisons
#         total = len(merged) * len(compare_cols)
#         print(f"Total comparisons: {total}")

#         exceptions = []
#         for col in compare_cols:
#             old_col = f"{col}_old"
#             new_col = f"{col}_new"
#             rules = (cfg or {}).get('fields', {}).get(col, {})

#             # Skip if explicitly ignored
#             if rules.get('type') == 'ignore':
#                 continue

#             print(f"Processing column: {col} with rules: {rules}")

#             # String fuzzy match
#             if rules.get('type') == 'string' and 'fuzzy_match' in rules:
#                 thresh = rules['fuzzy_match']
#                 for idx in merged.index:
#                     try:
#                         o = merged.loc[idx, old_col]
#                         n = merged.loc[idx, new_col]
                        
#                         # Handle null values properly
#                         if pd.isna(o) and pd.isna(n):
#                             continue  # Both null = match
#                         elif pd.isna(o) or pd.isna(n):
#                             # One null, one not = mismatch
#                             pk_values = get_pk_values(merged, idx, pk_cols)
#                             exceptions.append({
#                                 **pk_values,
#                                 "field": col,
#                                 "old": o,
#                                 "new": n,
#                             })
#                         elif fuzz.ratio(str(o), str(n)) < thresh:
#                             pk_values = get_pk_values(merged, idx, pk_cols)
#                             exceptions.append({
#                                 **pk_values,
#                                 "field": col,
#                                 "old": o,
#                                 "new": n,
#                             })
#                     except Exception as e:
#                         print(f"Error processing fuzzy match for {col} at index {idx}: {e}")
#                         continue

#             # Decimal tolerance
#             elif rules.get('type') == 'decimal' and 'tolerance' in rules:
#                 tol = rules['tolerance']
#                 for idx in merged.index:
#                     try:
#                         o = merged.loc[idx, old_col]
#                         n = merged.loc[idx, new_col]
                        
#                         # Handle null values properly
#                         if pd.isna(o) and pd.isna(n):
#                             continue  # Both null = match
#                         elif pd.isna(o) or pd.isna(n):
#                             # One null, one not = mismatch
#                             pk_values = get_pk_values(merged, idx, pk_cols)
#                             exceptions.append({
#                                 **pk_values,
#                                 "field": col,
#                                 "old": o,
#                                 "new": n,
#                             })
#                         else:
#                             try:
#                                 if abs(float(o) - float(n)) > tol:
#                                     pk_values = get_pk_values(merged, idx, pk_cols)
#                                     exceptions.append({
#                                         **pk_values,
#                                         "field": col,
#                                         "old": o,
#                                         "new": n,
#                                     })
#                             except (ValueError, TypeError):
#                                 # Can't convert to float = mismatch
#                                 pk_values = get_pk_values(merged, idx, pk_cols)
#                                 exceptions.append({
#                                     **pk_values,
#                                     "field": col,
#                                     "old": o,
#                                     "new": n,
#                                 })
#                     except Exception as e:
#                         print(f"Error processing decimal comparison for {col} at index {idx}: {e}")
#                         continue

#             # Default exact compare
#             else:
#                 try:
#                     diff_mask = merged[old_col].fillna('__NA__') != merged[new_col].fillna('__NA__')
#                     for idx in merged[diff_mask].index:
#                         try:
#                             pk_values = get_pk_values(merged, idx, pk_cols)
#                             exceptions.append({
#                                 **pk_values,
#                                 "field": col,
#                                 "old": merged.loc[idx, old_col],
#                                 "new": merged.loc[idx, new_col],
#                             })
#                         except Exception as e:
#                             print(f"Error creating exception for {col} at index {idx}: {e}")
#                             continue
#                 except Exception as e:
#                     print(f"Error in exact comparison for column {col}: {e}")
#                     continue

#         # 4) Calculate match percentage properly
#         n_exceptions = len(exceptions)
#         match_pct = round(100 * (total - n_exceptions) / total, 2) if total else 0.0
        
#         print(f"Comparison completed. Exceptions: {n_exceptions}, Match %: {match_pct}")
#         return {"match_pct": match_pct, "exceptions": exceptions}
        
#     except Exception as e:
#         print(f"Critical error in run_compare: {e}")
#         import traceback
#         traceback.print_exc()
#         raise

# def get_pk_values(merged_df, idx, pk_cols):
#     """
#     Safely extract primary key values from merged dataframe.
#     """
#     pk_values = {}
#     for k in pk_cols:
#         try:
#             # Primary key columns should exist without suffix after merge
#             if k in merged_df.columns:
#                 pk_values[k] = merged_df.loc[idx, k]
#             else:
#                 # Fallback: try to find the column with suffix
#                 if f"{k}_old" in merged_df.columns:
#                     pk_values[k] = merged_df.loc[idx, f"{k}_old"]
#                 elif f"{k}_new" in merged_df.columns:
#                     pk_values[k] = merged_df.loc[idx, f"{k}_new"]
#                 else:
#                     pk_values[k] = "Unknown"
#         except Exception as e:
#             print(f"Error getting PK value for {k}: {e}")
#             pk_values[k] = "Error"
    
#     return pk_values

import pandas as pd
from rapidfuzz import fuzz

def run_compare(df_old, df_new, pk_cols, cfg=None):
    """
    Compare df_old vs. df_new on the key(s) in pk_cols.
    Returns dict with match_pct and exceptions list.
    
    Args:
        df_old: Old dataset
        df_new: New dataset 
        pk_cols: Primary key column(s) for joining
        cfg: Configuration dict with comparison rules and null handling
    
    Config options:
        - ignore_nulls: If True, null vs null = match, null vs value = ignore
        - include_missing_records: If True, include missing records as exceptions
        - fields: Field-specific comparison rules
    """
    try:
        print(f"Starting comparison with PK columns: {pk_cols}")
        print(f"Old DF shape: {df_old.shape}, New DF shape: {df_new.shape}")
        
        # Get configuration settings with defaults
        ignore_nulls = (cfg or {}).get('ignore_nulls', False)
        include_missing_records = (cfg or {}).get('include_missing_records', False)
        
        print(f"Configuration - ignore_nulls: {ignore_nulls}, include_missing_records: {include_missing_records}")
        
        # 1) Merge to find what records exist where
        merged = df_old.merge(
            df_new,
            on=pk_cols,
            suffixes=('_old', '_new'),
            how='outer',
            indicator=True
        )
        print(f"Merged DF shape: {merged.shape}")
        
        # 2) Split into different categories
        both_records = merged[merged['_merge'] == 'both'].copy()
        old_only = merged[merged['_merge'] == 'left_only'].copy()
        new_only = merged[merged['_merge'] == 'right_only'].copy()
        
        print(f"Records in both: {len(both_records)}")
        print(f"Records only in old: {len(old_only)}")
        print(f"Records only in new: {len(new_only)}")
        
        # 3) Get columns to compare (exclude PKs)
        compare_cols = [c for c in df_old.columns if c not in pk_cols]
        print(f"Columns to compare: {compare_cols}")
        
        exceptions = []
        
        # 4) Handle missing records based on configuration
        if include_missing_records:
            # Add missing records as exceptions
            for idx in old_only.index:
                pk_vals = {k: old_only.loc[idx, k] for k in pk_cols}
                exceptions.append({
                    **pk_vals,
                    "field": "_record_status",
                    "old": "EXISTS",
                    "new": "MISSING",
                    "change_type": "deleted_record"
                })
            
            for idx in new_only.index:
                pk_vals = {k: new_only.loc[idx, k] for k in pk_cols}
                exceptions.append({
                    **pk_vals,
                    "field": "_record_status", 
                    "old": "MISSING",
                    "new": "EXISTS",
                    "change_type": "added_record"
                })
        else:
            # Just log missing records for information
            print(f"Records only in old (deleted): {len(old_only)}")
            print(f"Records only in new (added): {len(new_only)}")
        
        # 5) Compare fields for records that exist in both
        field_exceptions = 0
        
        for col in compare_cols:
            old_col = f"{col}_old"
            new_col = f"{col}_new"
            rules = (cfg or {}).get('fields', {}).get(col, {})
            
            # Skip ignored fields
            if rules.get('type') == 'ignore':
                print(f"Skipping ignored column: {col}")
                continue
            
            print(f"Comparing column: {col}")
            
            # Apply comparison rules
            if rules.get('type') == 'string' and 'fuzzy_match' in rules:
                # Fuzzy string comparison
                threshold = rules['fuzzy_match']
                mismatches = _find_fuzzy_mismatches(both_records, old_col, new_col, threshold, ignore_nulls)
                
            elif rules.get('type') == 'decimal' and 'tolerance' in rules:
                # Decimal tolerance comparison
                tolerance = rules['tolerance']
                mismatches = _find_decimal_mismatches(both_records, old_col, new_col, tolerance, ignore_nulls)
                
            else:
                # Exact comparison (default)
                mismatches = _find_exact_mismatches(both_records, old_col, new_col, ignore_nulls)
            
            # Add mismatches to exceptions (SAME FORMAT AS BEFORE)
            for idx in mismatches:
                pk_vals = {k: both_records.loc[idx, k] for k in pk_cols}
                exceptions.append({
                    **pk_vals,
                    "field": col,
                    "old": both_records.loc[idx, old_col],
                    "new": both_records.loc[idx, new_col]
                    # NO change_type field - keeps same format as before
                })
                field_exceptions += 1
        
        # 6) Calculate accurate match percentage
        # Only count field comparisons for records that exist in both datasets
        active_compare_cols = [c for c in compare_cols 
                              if (cfg or {}).get('fields', {}).get(c, {}).get('type') != 'ignore']
        
        total_field_comparisons = len(both_records) * len(active_compare_cols)
        
        if total_field_comparisons > 0:
            match_pct = round(100 * (total_field_comparisons - field_exceptions) / total_field_comparisons, 2)
        else:
            match_pct = 100.0  # No comparisons = perfect match
        
        print(f"Comparison completed:")
        print(f"  - Field exceptions: {field_exceptions}")
        print(f"  - Total exceptions: {len(exceptions)}")
        print(f"  - Match percentage: {match_pct}%")
        
        return {
            "match_pct": match_pct, 
            "exceptions": exceptions
        }
        
    except Exception as e:
        print(f"Critical error in run_compare: {e}")
        import traceback
        traceback.print_exc()
        raise

def _find_exact_mismatches(df, old_col, new_col, ignore_nulls=False):
    """Find rows where values don't match exactly."""
    try:
        mismatches = []
        for idx in df.index:
            old_val = df.loc[idx, old_col]
            new_val = df.loc[idx, new_col]
            
            # Handle null values based on configuration
            if pd.isna(old_val) and pd.isna(new_val):
                continue  # Both null = always match
            elif pd.isna(old_val) or pd.isna(new_val):
                if ignore_nulls:
                    continue  # Ignore null vs value differences
                else:
                    mismatches.append(idx)  # Null vs value = mismatch
            else:
                # Both have values - compare them
                if old_val != new_val:
                    mismatches.append(idx)
        
        return mismatches
    except Exception as e:
        print(f"Error in exact comparison: {e}")
        return []

def _find_fuzzy_mismatches(df, old_col, new_col, threshold, ignore_nulls=False):
    """Find rows where fuzzy match is below threshold."""
    mismatches = []
    try:
        for idx in df.index:
            old_val = df.loc[idx, old_col]
            new_val = df.loc[idx, new_col]
            
            # Handle null values based on configuration
            if pd.isna(old_val) and pd.isna(new_val):
                continue  # Both null = match
            elif pd.isna(old_val) or pd.isna(new_val):
                if ignore_nulls:
                    continue  # Ignore null vs value differences
                else:
                    mismatches.append(idx)  # Null vs value = mismatch
            else:
                # Compare using fuzzy ratio
                if fuzz.ratio(str(old_val), str(new_val)) < threshold:
                    mismatches.append(idx)
    except Exception as e:
        print(f"Error in fuzzy comparison: {e}")
    
    return mismatches

def _find_decimal_mismatches(df, old_col, new_col, tolerance, ignore_nulls=False):
    """Find rows where decimal difference exceeds tolerance."""
    mismatches = []
    try:
        for idx in df.index:
            old_val = df.loc[idx, old_col]
            new_val = df.loc[idx, new_col]
            
            # Handle null values based on configuration
            if pd.isna(old_val) and pd.isna(new_val):
                continue  # Both null = match
            elif pd.isna(old_val) or pd.isna(new_val):
                if ignore_nulls:
                    continue  # Ignore null vs value differences
                else:
                    mismatches.append(idx)  # Null vs value = mismatch
            else:
                try:
                    if abs(float(old_val) - float(new_val)) > tolerance:
                        mismatches.append(idx)
                except (ValueError, TypeError):
                    # Can't convert to numbers = mismatch
                    mismatches.append(idx)
    except Exception as e:
        print(f"Error in decimal comparison: {e}")
    
    return mismatches

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