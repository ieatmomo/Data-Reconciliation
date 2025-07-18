from rapidfuzz import fuzz

def run_compare(df_old, df_new, pk_cols, cfg=None):
    """
    Compare df_old vs. df_new on the key(s) in pk_cols, applying cfg for tolerances/fuzzy rules.
    Returns a dict with match_pct and a list of exception dicts.
    """
    # 1) Merge on the detected PK(s)
    merged = df_old.merge(
        df_new,
        on=pk_cols,
        suffixes=('_old', '_new'),
        how='outer',
        indicator=True
    )

    # 2) Determine which columns to compare (exclude PKs)
    compare_cols = [c for c in df_old.columns if c not in pk_cols]

    # 3) Compute total possible comparisons
    total = len(merged) * len(compare_cols)

    exceptions = []
    for col in compare_cols:
        old_col = f"{col}_old"
        new_col = f"{col}_new"
        rules = (cfg or {}).get('fields', {}).get(col, {})

        # Skip if explicitly ignored
        if rules.get('type') == 'ignore':
            continue

        # String fuzzy match
        if rules.get('type') == 'string' and 'fuzzy_match' in rules:
            thresh = rules['fuzzy_match']
            for idx, o, n in zip(merged.index, merged[old_col], merged[new_col]):
                if fuzz.ratio(str(o), str(n)) < thresh:
                    exceptions.append({
                        **{k: merged.loc[idx, k] for k in pk_cols},
                        "field": col,
                        "old": o,
                        "new": n,
                    })

        # Decimal tolerance
        elif rules.get('type') == 'decimal' and 'tolerance' in rules:
            tol = rules['tolerance']
            for idx, o, n in zip(merged.index, merged[old_col], merged[new_col]):
                try:
                    if abs(float(o) - float(n)) > tol:
                        exceptions.append({
                            **{k: merged.loc[idx, k] for k in pk_cols},
                            "field": col,
                            "old": o,
                            "new": n,
                        })
                except Exception:
                    exceptions.append({
                        **{k: merged.loc[idx, k] for k in pk_cols},
                        "field": col,
                        "old": o,
                        "new": n,
                    })

        # Default exact compare
        else:
            diff_mask = merged[old_col].fillna('__NA__') != merged[new_col].fillna('__NA__')
            for idx in merged[diff_mask].index:
                exceptions.append({
                    **{k: merged.loc[idx, k] for k in pk_cols},
                    "field": col,
                    "old": merged.loc[idx, old_col],
                    "new": merged.loc[idx, new_col],
                })

    # 4) Calculate match percentage properly
    n_exceptions = len(exceptions)
    match_pct = round(100 * (total - n_exceptions) / total, 2) if total else 0.0

    return {"match_pct": match_pct, "exceptions": exceptions}
