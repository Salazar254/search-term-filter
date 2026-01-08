import pandas as pd
import argparse
import sys
import os
from datetime import datetime
import warnings
import csv
import chardet  # For detecting file encoding
warnings.filterwarnings('ignore')

# Try to import PDF libraries (optional)
try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("Note: PDF support not available. Install pdfplumber for PDF support.")

def detect_file_type(filepath):
    """Detect file type based on extension"""
    ext = os.path.splitext(filepath)[1].lower()
    return ext

def detect_encoding(filepath):
    """Detect file encoding"""
    try:
        with open(filepath, 'rb') as f:
            raw_data = f.read(10000)  # Read first 10KB to detect encoding
            result = chardet.detect(raw_data)
            return result['encoding']
    except:
        return 'utf-8'  # Default to utf-8

def read_data_file(filepath, file_type=None):
    """
    Read data from various file formats
    Supports: .csv, .xlsx, .xls, .pdf
    """
    if file_type is None:
        file_type = detect_file_type(filepath)
    
    print(f"Reading {file_type} file: {filepath}")
    
    try:
        if file_type == '.csv':
            # Detect encoding first
            encoding = detect_encoding(filepath)
            print(f"  Detected encoding: {encoding}")
            
            # Try different CSV reading strategies
            try:
                # First try with detected encoding
                df = pd.read_csv(filepath, encoding=encoding, on_bad_lines='skip')
            except Exception as e:
                print(f"  Read with {encoding} failed: {e}")
                # Try common encodings
                encodings_to_try = ['utf-8', 'latin1', 'ISO-8859-1', 'cp1252', 'utf-16', 'utf-16-le']
                for enc in encodings_to_try:
                    if enc == encoding:
                        continue  # Already tried
                    try:
                        print(f"  Trying {enc} encoding...")
                        df = pd.read_csv(filepath, encoding=enc, on_bad_lines='skip')
                        print(f"  Success with {enc} encoding")
                        break
                    except:
                        continue
                else:
                    # If all else fails, use Python's csv module
                    print("  All encoding attempts failed, using csv module fallback...")
                    rows = []
                    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                        reader = csv.reader(f)
                        try:
                            headers = next(reader)
                        except StopIteration:
                            raise ValueError("CSV file is empty")
                        
                        for i, row in enumerate(reader):
                            if len(row) != len(headers):
                                # Pad or truncate row to match headers
                                if len(row) > len(headers):
                                    row = row[:len(headers)]
                                else:
                                    row = row + [''] * (len(headers) - len(row))
                            rows.append(row)
                    
                    df = pd.DataFrame(rows, columns=headers)
            
            # Clean the DataFrame
            df = df.dropna(how='all')  # Remove completely empty rows
            df = df.reset_index(drop=True)
        
        elif file_type in ['.xlsx', '.xls']:
            df = pd.read_excel(filepath)
            df = df.dropna(how='all')  # Remove completely empty rows
            df = df.reset_index(drop=True)
        
        elif file_type == '.pdf':
            if not PDF_SUPPORT:
                raise ImportError("PDF support requires pdfplumber. Install with: pip install pdfplumber")
            
            # Extract tables from PDF
            with pdfplumber.open(filepath) as pdf:
                tables = []
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
                
                if not tables:
                    raise ValueError("No tables found in PDF")
                
                # Convert first table to DataFrame
                df = pd.DataFrame(tables[0])
                
                # Use first row as header if it looks like column names
                if df.shape[0] > 1:
                    df.columns = df.iloc[0]
                    df = df[1:].reset_index(drop=True)
        
        else:
            raise ValueError(f"Unsupported file format: {file_type}")
        
        print(f"  Successfully loaded. Shape: {df.shape}")
        return df
    
    except Exception as e:
        print(f"  Error reading file: {e}")
        raise

def normalize_column_names(df, file_type='search_terms'):
    """
    Normalize column names to expected format
    """
    # Create a mapping of possible column names to expected names
    column_mappings = {
        'search_terms': {
            'expected': 'Search term',
            'variations': ['Search term', 'Search Term', 'Search keyword', 
                          'Keyword', 'search_term', 'search term', 'search',
                          'Search query', 'Query', 'Search terms', 'Search terms report']
        },
        'clicks': {
            'expected': 'Clicks',
            'variations': ['Clicks', 'clicks', 'Click', 'click']
        },
        'impressions': {
            'expected': 'Impressions',
            'variations': ['Impressions', 'impressions', 'Impr.', 'Impressions (Top) %']
        }
    }
    
    df_columns = [str(col).strip() for col in df.columns]
    
    # For search terms file
    if file_type == 'search_terms':
        # Try to find search term column
        search_term_col = None
        for col in df_columns:
            for variation in column_mappings['search_terms']['variations']:
                if variation.lower() in col.lower():
                    search_term_col = col
                    break
            if search_term_col:
                break
        
        if search_term_col:
            df = df.rename(columns={search_term_col: 'Search term'})
            print(f"  Found search term column: '{search_term_col}' -> 'Search term'")
        else:
            # If no match found, check if first column looks like search terms
            if len(df_columns) > 0:
                # Safely convert to string and check samples
                try:
                    sample_data = df.iloc[:5, 0].fillna('').astype(str)
                    # Check if sample data looks like search queries (has spaces or is long)
                    if sample_data.str.contains(' ').any() or sample_data.str.len().max() > 10:
                        print(f"  Using first column as search term: '{df_columns[0]}'")
                        df = df.rename(columns={df_columns[0]: 'Search term'})
                    else:
                        raise ValueError(f"Could not find search term column. Available columns: {df_columns}")
                except:
                    # If .str methods fail, just use first column
                    print(f"  Using first column as search term (fallback): '{df_columns[0]}'")
                    df = df.rename(columns={df_columns[0]: 'Search term'})
            else:
                raise ValueError(f"DataFrame has no columns")
    
    # For negative keywords file
    elif file_type == 'negatives':
        # Try to find negative keyword column
        keyword_col = None
        match_type_col = None
        
        for col in df_columns:
            col_lower = col.lower()
            if any(term in col_lower for term in ['negative', 'keyword', 'match']):
                keyword_col = col
            elif 'match' in col_lower and 'type' in col_lower:
                match_type_col = col
        
        if keyword_col:
            df = df.rename(columns={keyword_col: 'negative_keyword'})
            print(f"  Found negative keyword column: '{keyword_col}' -> 'negative_keyword'")
        
        if match_type_col:
            df = df.rename(columns={match_type_col: 'match_type'})
            print(f"  Found match type column: '{match_type_col}' -> 'match_type'")
        else:
            # Try to infer match type column
            for col in df_columns:
                if col.lower() in ['type', 'match', 'campaign']:
                    match_type_col = col
                    df = df.rename(columns={col: 'match_type'})
                    print(f"  Inferred match type column: '{col}' -> 'match_type'")
                    break
    
    return df

def load_search_terms(filepath):
    """Load and normalize search terms file"""
    df = read_data_file(filepath)
    df = normalize_column_names(df, 'search_terms')
    
    # Ensure required columns exist
    required = ['Search term']
    optional = ['Clicks', 'Impressions']
    
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Search terms file missing required column: '{col}'")
    
    # Fill optional columns if missing
    for col in optional:
        if col not in df.columns:
            df[col] = 0
            print(f"  Added missing column: {col}")
    
    return df

def load_negatives(filepath):
    """Load and normalize negative keywords file"""
    df = read_data_file(filepath)
    df = normalize_column_names(df, 'negatives')
    
    # Ensure required columns
    if 'negative_keyword' not in df.columns:
        # Try to use first column as negative_keyword
        df = df.rename(columns={df.columns[0]: 'negative_keyword'})
        print(f"  Using first column as negative_keyword: '{df.columns[0]}'")
    
    if 'match_type' not in df.columns:
        # Default to BROAD match type
        df['match_type'] = 'BROAD'
        print("  Added default match_type: BROAD")
    
    # Clean up data - safely convert to string
    neg_kw = df['negative_keyword'].fillna('').astype(str)
    df['negative_keyword'] = neg_kw.str.strip() if isinstance(neg_kw, pd.Series) else neg_kw.apply(lambda x: str(x).strip())
    if 'match_type' in df.columns:
        match_t = df['match_type'].fillna('BROAD').astype(str)
        df['match_type'] = match_t.str.strip().str.upper() if isinstance(match_t, pd.Series) else match_t.apply(lambda x: str(x).strip().upper())
    
    return df

def filter_search_terms(terms_df, negatives_df):
    """Filter search terms based on negative keywords"""
    print("Filtering terms...")
    
    # Prepare results
    results = []
    audit_trail = []
    
    for _, term_row in terms_df.iterrows():
        # Safely get search term
        search_term = str(term_row.get('Search term', '')).strip().lower()
        if pd.isna(search_term) or search_term == 'nan':
            search_term = ''
        
        excluded = False
        exclusion_reason = ""
        matched_negative = ""
        matched_type = ""
        
        for _, neg_row in negatives_df.iterrows():
            negative = str(neg_row.get('negative_keyword', '')).strip().lower()
            if pd.isna(negative) or negative == 'nan':
                continue
            
            match_type = neg_row.get('match_type', 'BROAD')
            match_type = str(match_type).strip().upper() if not pd.isna(match_type) else 'BROAD'
            
            # Skip if search term or negative is empty
            if not search_term or not negative:
                continue
            
            # Apply match type logic
            if match_type == 'EXACT':
                if search_term == negative:
                    excluded = True
                    exclusion_reason = f"Excluded by EXACT negative: {neg_row['negative_keyword']}"
                    matched_negative = neg_row['negative_keyword']
                    matched_type = match_type
                    break
            
            elif match_type == 'PHRASE':
                if negative in search_term:
                    excluded = True
                    exclusion_reason = f"Excluded by PHRASE negative: {neg_row['negative_keyword']}"
                    matched_negative = neg_row['negative_keyword']
                    matched_type = match_type
                    break
            
            elif match_type == 'BROAD':
                # Check if any word from negative appears in search term
                neg_words = negative.split()
                term_words = search_term.split()
                if any(word in term_words for word in neg_words):
                    excluded = True
                    exclusion_reason = f"Excluded by BROAD negative: {neg_row['negative_keyword']}"
                    matched_negative = neg_row['negative_keyword']
                    matched_type = match_type
                    break
        
        if not excluded:
            exclusion_reason = "Not matched by any negative"
        
        # Create result row
        result_row = term_row.to_dict()
        result_row['excluded_by_negatives'] = excluded
        result_row['exclusion_reason'] = exclusion_reason
        result_row['checked_at'] = datetime.now().isoformat()
        
        # Create audit row
        audit_row = result_row.copy()
        if excluded:
            audit_row['matched_negative_keyword'] = matched_negative
            audit_row['matched_negative_match_type'] = matched_type
        else:
            audit_row['matched_negative_keyword'] = ''
            audit_row['matched_negative_match_type'] = ''
        
        results.append(result_row)
        audit_trail.append(audit_row)
    
    # Convert to DataFrames
    results_df = pd.DataFrame(results)
    audit_df = pd.DataFrame(audit_trail)
    
    # Separate excluded and included terms
    excluded_count = results_df['excluded_by_negatives'].sum()
    remaining_count = len(results_df) - excluded_count
    
    print(f"Filtering complete. Excluded {excluded_count} terms. Remaining {remaining_count} terms.")
    
    return results_df, audit_df

def main():
    parser = argparse.ArgumentParser(description='Filter search terms using negative keywords')
    parser.add_argument('--terms', required=True, help='Search terms file (CSV, Excel, or PDF)')
    parser.add_argument('--negatives', required=True, help='Negative keywords file (CSV, Excel, or PDF)')
    parser.add_argument('--output', required=True, help='Output CSV file for review')
    parser.add_argument('--audit-output', help='Output CSV file for audit trail')
    parser.add_argument('--analyze-output', help='Output CSV file for analysis')
    parser.add_argument('--editor-export', help='Export format for Google Ads Editor')
    
    args = parser.parse_args()
    
    try:
        # Load data
        print(f"Loading search terms from: {args.terms}")
        terms_df = load_search_terms(args.terms)
        
        print(f"Loading negatives from: {args.negatives}")
        negatives_df = load_negatives(args.negatives)
        
        print(f"Loaded {len(terms_df)} search terms and {len(negatives_df)} negatives.")
        
        # Filter terms
        results_df, audit_df = filter_search_terms(terms_df, negatives_df)
        
        # Save outputs
        print(f"Saving review output to: {args.output}")
        results_df.to_csv(args.output, index=False)
        
        if args.audit_output:
            print(f"Saving audit output to: {args.audit_output}")
            audit_df.to_csv(args.audit_output, index=False)
        
        if args.analyze_output:
            print(f"Saving analysis output to: {args.analyze_output}")
            # Add analysis logic here if needed
            results_df.to_csv(args.analyze_output, index=False)
        
        print("Done.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
