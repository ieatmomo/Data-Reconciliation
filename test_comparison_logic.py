#!/usr/bin/env python3
"""
Test script to validate the comparison engine with different null handling configurations.
"""

import pandas as pd
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from analysis.compare import run_compare

def create_test_data():
    """Create test datasets with various scenarios."""
    
    # Test data with nulls, exact matches, and differences
    df_old = pd.DataFrame({
        'id': [1, 2, 3, 4, 5, 6],
        'name': ['John', 'Jane', 'Bob', 'Alice', None, 'Charlie'],
        'age': [25, 30, None, 40, 35, 45],
        'score': [85.5, 90.0, 75.5, 88.0, 92.0, None]
    })
    
    df_new = pd.DataFrame({
        'id': [1, 2, 3, 4, 5, 6],
        'name': ['John', 'Jane Doe', 'Bob', None, 'Eve', 'Charlie'],
        'age': [25, 31, 35, 40, 35, None],
        'score': [85.5, 90.0, 75.5, 89.0, None, 95.0]
    })
    
    return df_old, df_new

def test_null_handling():
    """Test different null handling configurations."""
    
    print("=" * 60)
    print("TESTING COMPARISON ENGINE NULL HANDLING")
    print("=" * 60)
    
    df_old, df_new = create_test_data()
    pk_cols = ['id']
    
    print("\nOLD DATASET:")
    print(df_old)
    print("\nNEW DATASET:")
    print(df_new)
    
    # Configuration 1: Treat null vs value as exceptions
    print("\n" + "="*50)
    print("TEST 1: NULL VS VALUE = EXCEPTION")
    print("="*50)
    
    cfg_strict = {
        'ignore_nulls': False,
        'include_missing_records': False,
        'fields': {
            'name': {'type': 'string', 'fuzzy_match': 90},
            'age': {'type': 'decimal', 'tolerance': 1.0},
            'score': {'type': 'decimal', 'tolerance': 0.1}
        }
    }
    
    result_strict = run_compare(df_old, df_new, pk_cols, cfg_strict)
    print(f"\nRESULTS (Strict null handling):")
    print(f"Match percentage: {result_strict['match_pct']}%")
    print(f"Number of exceptions: {len(result_strict['exceptions'])}")
    print("\nExceptions:")
    for exc in result_strict['exceptions']:
        print(f"  ID {exc['id']}: {exc['field']} - '{exc['old']}' -> '{exc['new']}'")
    
    # Configuration 2: Ignore null vs value differences
    print("\n" + "="*50)
    print("TEST 2: NULL VS VALUE = IGNORED")
    print("="*50)
    
    cfg_lenient = {
        'ignore_nulls': True,
        'include_missing_records': False,
        'fields': {
            'name': {'type': 'string', 'fuzzy_match': 90},
            'age': {'type': 'decimal', 'tolerance': 1.0},
            'score': {'type': 'decimal', 'tolerance': 0.1}
        }
    }
    
    result_lenient = run_compare(df_old, df_new, pk_cols, cfg_lenient)
    print(f"\nRESULTS (Lenient null handling):")
    print(f"Match percentage: {result_lenient['match_pct']}%")
    print(f"Number of exceptions: {len(result_lenient['exceptions'])}")
    print("\nExceptions:")
    for exc in result_lenient['exceptions']:
        print(f"  ID {exc['id']}: {exc['field']} - '{exc['old']}' -> '{exc['new']}'")
    
    # Configuration 3: Include missing records
    print("\n" + "="*50)
    print("TEST 3: INCLUDING MISSING RECORDS")
    print("="*50)
    
    # Create test data with missing records
    df_old_missing = pd.DataFrame({
        'id': [1, 2, 3, 4],
        'name': ['John', 'Jane', 'Bob', 'Alice'],
        'score': [85.5, 90.0, 75.5, 88.0]
    })
    
    df_new_missing = pd.DataFrame({
        'id': [1, 2, 5, 6],  # Missing 3,4 and added 5,6
        'name': ['John', 'Jane Doe', 'Eve', 'Charlie'],
        'score': [85.5, 90.0, 92.0, 95.0]
    })
    
    cfg_with_missing = {
        'ignore_nulls': False,
        'include_missing_records': True,
        'fields': {
            'name': {'type': 'string', 'fuzzy_match': 90},
            'score': {'type': 'decimal', 'tolerance': 0.1}
        }
    }
    
    result_missing = run_compare(df_old_missing, df_new_missing, pk_cols, cfg_with_missing)
    print(f"\nRESULTS (Including missing records):")
    print(f"Match percentage: {result_missing['match_pct']}%")
    print(f"Number of exceptions: {len(result_missing['exceptions'])}")
    print("\nExceptions:")
    for exc in result_missing['exceptions']:
        if 'change_type' in exc:
            print(f"  ID {exc['id']}: {exc['field']} - {exc['change_type']}")
        else:
            print(f"  ID {exc['id']}: {exc['field']} - '{exc['old']}' -> '{exc['new']}'")

def test_comparison_types():
    """Test different comparison types (exact, fuzzy, decimal)."""
    
    print("\n" + "="*60)
    print("TESTING COMPARISON TYPES")
    print("="*60)
    
    df_old = pd.DataFrame({
        'id': [1, 2, 3],
        'exact_field': ['ABC', 'DEF', 'GHI'],
        'fuzzy_field': ['Hello World', 'Test String', 'Another Test'],
        'decimal_field': [10.00, 20.50, 30.25]
    })
    
    df_new = pd.DataFrame({
        'id': [1, 2, 3],
        'exact_field': ['ABC', 'DEF', 'XYZ'],  # One change
        'fuzzy_field': ['Hello World!', 'Test String', 'Another Tests'],  # Minor changes
        'decimal_field': [10.01, 20.50, 30.20]  # Small decimal changes
    })
    
    cfg_types = {
        'ignore_nulls': False,
        'fields': {
            'exact_field': {'type': 'string'},  # No fuzzy match = exact comparison
            'fuzzy_field': {'type': 'string', 'fuzzy_match': 90},  # Fuzzy comparison
            'decimal_field': {'type': 'decimal', 'tolerance': 0.05}  # Decimal tolerance
        }
    }
    
    result = run_compare(df_old, df_new, ['id'], cfg_types)
    print(f"\nRESULTS:")
    print(f"Match percentage: {result['match_pct']}%")
    print(f"Number of exceptions: {len(result['exceptions'])}")
    print("\nExceptions:")
    for exc in result['exceptions']:
        print(f"  ID {exc['id']}: {exc['field']} - '{exc['old']}' -> '{exc['new']}'")

if __name__ == "__main__":
    try:
        test_null_handling()
        test_comparison_types()
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
