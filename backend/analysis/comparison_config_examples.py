# Data Reconciliation Engine - Configuration Examples
# This file shows different configuration options for null handling and comparison rules

# ============================================================================
# EXAMPLE 1: STRICT NULL HANDLING (null vs value = exception)
# ============================================================================
# Use this when data quality is critical and any null mismatches should be flagged

strict_null_config = {
    # Null handling: False means null vs value differences are treated as exceptions
    'ignore_nulls': False,
    
    # Missing records: False means only compare field differences for matching records
    'include_missing_records': False,
    
    # Field-specific comparison rules
    'fields': {
        'name': {
            'type': 'string',
            'fuzzy_match': 90  # 90% similarity threshold for string matching
        },
        'price': {
            'type': 'decimal',
            'tolerance': 0.01  # Allow $0.01 difference
        },
        'date': {
            'type': 'date',
            'formats': ['%Y-%m-%d', '%d %b %Y']
        },
        'category': {
            'type': 'string',
            'fuzzy_match': 95  # Higher threshold for categories
        },
        'vendor': {
            'type': 'ignore'  # Skip this field entirely
        }
    }
}

# ============================================================================
# EXAMPLE 2: LENIENT NULL HANDLING (null vs value = ignored)
# ============================================================================
# Use this when you want to focus on actual value changes, ignoring null differences

lenient_null_config = {
    # Null handling: True means null vs value differences are ignored
    'ignore_nulls': True,
    
    # Missing records: False means only compare field differences
    'include_missing_records': False,
    
    # Field-specific comparison rules
    'fields': {
        'name': {
            'type': 'string',
            'fuzzy_match': 80  # More lenient fuzzy matching
        },
        'price': {
            'type': 'decimal',
            'tolerance': 0.05  # Allow larger price differences
        },
        'quantity': {
            'type': 'integer'  # Exact integer comparison
        },
        'description': {
            'type': 'string',
            'fuzzy_match': 70  # Very lenient for descriptions
        }
    }
}

# ============================================================================
# EXAMPLE 3: COMPREHENSIVE TRACKING (includes missing records)
# ============================================================================
# Use this when you want to track both field changes AND record additions/deletions

comprehensive_config = {
    # Null handling: False means flag null vs value differences
    'ignore_nulls': False,
    
    # Missing records: True means include record additions/deletions as exceptions
    'include_missing_records': True,
    
    # Field-specific comparison rules
    'fields': {
        'name': {
            'type': 'string',
            'fuzzy_match': 85
        },
        'price': {
            'type': 'decimal',
            'tolerance': 0.02
        },
        'status': {
            'type': 'string'  # Exact string comparison (no fuzzy_match specified)
        }
    }
}

# ============================================================================
# EXAMPLE 4: MIXED APPROACH (lenient nulls but track missing records)
# ============================================================================
# Use this for a balanced approach: ignore null differences but track record changes

balanced_config = {
    # Null handling: True means ignore null vs value differences
    'ignore_nulls': True,
    
    # Missing records: True means track record additions/deletions
    'include_missing_records': True,
    
    # Field-specific comparison rules
    'fields': {
        'name': {
            'type': 'string',
            'fuzzy_match': 90
        },
        'price': {
            'type': 'decimal',
            'tolerance': 0.01
        },
        'date': {
            'type': 'date'
        }
    }
}

# ============================================================================
# HOW TO USE THESE CONFIGURATIONS
# ============================================================================

"""
Example usage in your code:

from analysis.compare import run_compare

# Load your datasets
df_old = pd.read_csv('old_data.csv')
df_new = pd.read_csv('new_data.csv')
pk_cols = ['id']  # Primary key columns

# Choose a configuration based on your needs
config = strict_null_config  # or lenient_null_config, etc.

# Run the comparison
result = run_compare(df_old, df_new, pk_cols, config)

# Results will include:
print(f"Match percentage: {result['match_pct']}%")
print(f"Number of exceptions: {len(result['exceptions'])}")

# Each exception will have:
for exc in result['exceptions']:
    if 'change_type' in exc:
        # This is a missing record
        print(f"Record {exc['id']}: {exc['change_type']}")
    else:
        # This is a field difference
        print(f"Record {exc['id']}: {exc['field']} changed from '{exc['old']}' to '{exc['new']}'")
"""

# ============================================================================
# CONFIGURATION FIELD TYPES
# ============================================================================

"""
Available field types and their options:

1. 'string' - Text comparison
   - fuzzy_match: Integer (0-100) - similarity threshold for fuzzy matching
   - If fuzzy_match not specified, exact comparison is used

2. 'decimal' - Numeric comparison with tolerance
   - tolerance: Float - maximum allowed difference

3. 'integer' - Whole number comparison
   - No additional options - exact comparison

4. 'date' - Date comparison
   - formats: List of date format strings for parsing

5. 'ignore' - Skip this field entirely
   - No additional options

6. No type specified - Default to exact comparison
"""
