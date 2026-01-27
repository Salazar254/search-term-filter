import pandas as pd
import argparse
import sys
import os
from datetime import datetime
import warnings
import csv
import chardet  # For detecting file encoding
import re
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
            # Prioritize 'negative_keyword' or similar keyword column
            if col_lower == 'negative_keyword' or (any(term in col_lower for term in ['negative']) and 'keyword' in col_lower):
                keyword_col = col
            # Find match type column
            elif col_lower == 'match_type' or ('match' in col_lower and 'type' in col_lower):
                match_type_col = col
        
        # If no explicit match type found, look for type/campaign columns
        if not match_type_col:
            for col in df_columns:
                col_lower = col.lower()
                if col_lower in ['type', 'match', 'campaign'] or 'match' in col_lower:
                    match_type_col = col
                    break
        
        # Rename columns to standard names
        if keyword_col and keyword_col != 'negative_keyword':
            df = df.rename(columns={keyword_col: 'negative_keyword'})
            print(f"  Found negative keyword column: '{keyword_col}' -> 'negative_keyword'")
        
        if match_type_col and match_type_col != 'match_type':
            df = df.rename(columns={match_type_col: 'match_type'})
            print(f"  Found match type column: '{match_type_col}' -> 'match_type'")
    
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

def normalize_text(text: str) -> str:
    """
    Normalizes a search term or negative keyword according to spec:
    1. Lowercase
    2. Trim whitespace
    3. Collapse multiple spaces
    4. Remove surrounding quotes/brackets
    """
    if not isinstance(text, str):
        return ""
    
    text = text.lower().strip()
    
    # Remove surrounding quotes (single or double) on the whole string
    if text.startswith('"') and text.endswith('"') and len(text) > 1:
        text = text[1:-1]
    elif text.startswith("'") and text.endswith("'") and len(text) > 1:
        text = text[1:-1]
    elif text.startswith("[") and text.endswith("]") and len(text) > 1:
        text = text[1:-1]
    
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def tokenize_text(text: str) -> list:
    """Splits text by space into tokens."""
    return text.split()

def is_phrase_match_token_aware(search_tokens: list, phrase_tokens: list) -> bool:
    """
    Checks for phrase match: phrase_tokens must appear as a contiguous sub-sequence
    in search_tokens. Token-aware to avoid false positives.
    """
    n_len = len(phrase_tokens)
    s_len = len(search_tokens)
    
    if n_len > s_len:
        return False
    
    for i in range(s_len - n_len + 1):
        if search_tokens[i : i + n_len] == phrase_tokens:
            return True
    
    return False

def filter_search_terms(terms_df, negatives_df):
    """Filter search terms based on negative keywords using optimized operations"""
    print("Filtering terms...")
    
    # Normalize and prepare data
    terms_df = terms_df.copy()
    negatives_df = negatives_df.copy()
    
    # Normalize search terms using proper normalization function
    terms_df['search_term_normalized'] = terms_df['Search term'].fillna('').astype(str).apply(normalize_text)
    terms_df['search_term_tokens'] = terms_df['search_term_normalized'].apply(tokenize_text)
    
    # Normalize negatives
    negatives_df['negative_normalized'] = negatives_df['negative_keyword'].fillna('').astype(str).apply(normalize_text)
    negatives_df['negative_tokens'] = negatives_df['negative_normalized'].apply(tokenize_text)
    negatives_df['match_type'] = negatives_df['match_type'].fillna('BROAD').astype(str).str.strip().str.upper()
    
    # Separate negatives by match type for efficient processing
    exact_negatives = []
    phrase_negatives = []
    broad_negatives = []
    
    for _, row in negatives_df.iterrows():
        neg_normalized = row['negative_normalized']
        neg_tokens = row['negative_tokens']
        neg_keyword = row['negative_keyword']
        match_type = row['match_type']
        
        if not neg_tokens:  # Skip empty
            continue
        
        if match_type == 'EXACT':
            exact_negatives.append((neg_normalized, neg_keyword))
        elif match_type == 'PHRASE':
            phrase_negatives.append((neg_tokens, neg_keyword))
        elif match_type == 'BROAD':
            broad_negatives.append((set(neg_tokens), neg_keyword))
    
    # Convert exact to set for O(1) lookup
    exact_set = {norm: orig for norm, orig in exact_negatives}
    
    # Initialize result columns
    terms_df['excluded_by_negatives'] = False
    terms_df['exclusion_reason'] = 'Not matched by any negative'
    terms_df['matched_negative_keyword'] = ''
    terms_df['matched_negative_match_type'] = ''
    
    # Process each search term
    for idx in terms_df.index:
        if terms_df.at[idx, 'excluded_by_negatives']:
            continue  # Already excluded
        
        search_normalized = terms_df.at[idx, 'search_term_normalized']
        search_tokens = terms_df.at[idx, 'search_term_tokens']
        
        if not search_tokens:
            continue
        
        # 1. Check EXACT matches (fastest - O(1) lookup)
        if search_normalized in exact_set:
            terms_df.at[idx, 'excluded_by_negatives'] = True
            terms_df.at[idx, 'exclusion_reason'] = f"Excluded by EXACT negative: {exact_set[search_normalized]}"
            terms_df.at[idx, 'matched_negative_keyword'] = exact_set[search_normalized]
            terms_df.at[idx, 'matched_negative_match_type'] = 'EXACT'
            continue
        
        # 2. Check PHRASE matches (token-aware to avoid false positives)
        for phrase_tokens, phrase_keyword in phrase_negatives:
            if is_phrase_match_token_aware(search_tokens, phrase_tokens):
                terms_df.at[idx, 'excluded_by_negatives'] = True
                terms_df.at[idx, 'exclusion_reason'] = f"Excluded by PHRASE negative: {phrase_keyword}"
                terms_df.at[idx, 'matched_negative_keyword'] = phrase_keyword
                terms_df.at[idx, 'matched_negative_match_type'] = 'PHRASE'
                break
        
        if terms_df.at[idx, 'excluded_by_negatives']:
            continue  # Already excluded by phrase
        
        # 3. Check BROAD matches (all words must be present)
        search_token_set = set(search_tokens)
        for broad_token_set, broad_keyword in broad_negatives:
            if broad_token_set.issubset(search_token_set):
                terms_df.at[idx, 'excluded_by_negatives'] = True
                terms_df.at[idx, 'exclusion_reason'] = f"Excluded by BROAD negative: {broad_keyword}"
                terms_df.at[idx, 'matched_negative_keyword'] = broad_keyword
                terms_df.at[idx, 'matched_negative_match_type'] = 'BROAD'
                break
    
    # Add timestamp
    terms_df['checked_at'] = datetime.now().isoformat()
    
    # Prepare result DataFrames
    # Primary output: only non-excluded terms (for manual review)
    results_df = terms_df[~terms_df['excluded_by_negatives']].copy()
    # Audit output: all terms with exclusion info
    audit_df = terms_df.copy()
    
    # Remove temporary columns
    cols_to_drop = ['search_term_normalized', 'search_term_tokens']
    results_df = results_df.drop(columns=cols_to_drop, errors='ignore')
    audit_df = audit_df.drop(columns=cols_to_drop, errors='ignore')
    
    # Ensure excluded_by_negatives is boolean
    results_df['excluded_by_negatives'] = results_df['excluded_by_negatives'].astype(bool)
    audit_df['excluded_by_negatives'] = audit_df['excluded_by_negatives'].astype(bool)
    
    # Separate excluded and included terms
    excluded_count = audit_df['excluded_by_negatives'].sum()
    remaining_count = len(results_df)
    
    print(f"Filtering complete. Excluded {excluded_count} terms. Remaining {remaining_count} terms for review.")
    
    return results_df, audit_df

def main():
    parser = argparse.ArgumentParser(description='Elite Google Ads Filter - ROI Optimization Engine')
    parser.add_argument('--terms', required=True, help='Search terms file (CSV, Excel, or PDF)')
    parser.add_argument('--negatives', required=True, help='Negative keywords file (CSV, Excel, or PDF)')
    parser.add_argument('--output', required=True, help='Output CSV file for review')
    parser.add_argument('--audit-output', help='Output CSV file for audit trail')
    parser.add_argument('--analyze-output', help='Output CSV file for analysis')
    parser.add_argument('--editor-export', help='Export format for Google Ads Editor')
    parser.add_argument('--analytics-output', help='Output JSON file for analytics dashboard')
    parser.add_argument('--suggestions-output', help='Output CSV file for auto-generated negative suggestions')
    
    args = parser.parse_args()
    
    try:
        # Load data
        # Validate input file paths and sizes
        MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
        
        for filepath in [args.terms, args.negatives]:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"File not found: {filepath}")
            file_size = os.path.getsize(filepath)
            if file_size > MAX_FILE_SIZE:
                raise ValueError(f"File too large ({file_size} bytes > {MAX_FILE_SIZE}): {filepath}")
            if file_size == 0:
                raise ValueError(f"File is empty: {filepath}")
        
        print(f"Loading search terms from: {args.terms}")
        terms_df = load_search_terms(args.terms)
        
        print(f"Loading negatives from: {args.negatives}")
        negatives_df = load_negatives(args.negatives)
        
        # Validate loaded data
        if terms_df.empty:
            raise ValueError("Search terms file is empty after loading")
        if negatives_df.empty:
            raise ValueError("Negatives file is empty after loading")
        
        print(f"Loaded {len(terms_df)} search terms and {len(negatives_df)} negatives.")
        
        # Filter terms
        results_df, audit_df = filter_search_terms(terms_df, negatives_df)
        
        # ELITE: Generate analytics and insights
        print("Analyzing performance metrics...")
        try:
            # Import from same package (ensure src directory is in path)
            src_dir = os.path.dirname(os.path.abspath(__file__))
            if src_dir not in sys.path:
                sys.path.insert(0, src_dir)
            from analytics import PerformanceAnalytics
            analytics = PerformanceAnalytics(terms_df, negatives_df, results_df)
            exec_summary = analytics.get_executive_summary()
        except Exception as e:
            print(f"Warning: Analytics engine error: {e}")
            # Calculate from audit_df which has all terms
            excluded_count = int(audit_df['excluded_by_negatives'].sum())
            total_count = len(audit_df)
            exec_summary = {
                'metrics': {'cost_waste_prevented': 0, 'cost_reduction_percentage': 0, 'quality_score': 0, 'action_score': 0},
                'total_terms_analyzed': total_count,
                'terms_excluded': excluded_count,
                'terms_remaining': total_count - excluded_count,
                'recommendation': []
            }
        
        # ELITE: Auto-generate negative suggestions
        print("Generating AI negative keyword suggestions...")
        try:
            # Import from same package
            from auto_negative import AutoNegativeEngine
            auto_neg = AutoNegativeEngine(terms_df)
            auto_suggestions = auto_neg.generate_suggestions(threshold=65)
            impact = auto_neg.get_impact_summary()
        except Exception as e:
            print(f"Warning: Auto-negative engine error: {e}")
            auto_suggestions = []
            impact = {'total_suggested': 0, 'potential_cost_savings': 0, 'potential_impression_reduction': 0, 'top_priority': None}
        
        # Print elite metrics to console
        print("\n" + "="*60)
        print("ELITE PERFORMANCE METRICS")
        print("="*60)
        print(f"Cost Waste Prevented: ${exec_summary['metrics'].get('cost_waste_prevented', 0):,.2f}")
        print(f"Cost Reduction: {exec_summary['metrics'].get('cost_reduction_percentage', 0):.1f}%")
        print(f"Terms Excluded: {exec_summary['terms_excluded']} / {exec_summary['total_terms_analyzed']}")
        print(f"Quality Score: {exec_summary['metrics'].get('quality_score', 0):.1f}%")
        print(f"Action Score: {exec_summary['metrics'].get('action_score', 0)}/100")
        print(f"\nAI Suggestions: {impact.get('total_suggested', 0)} new negatives identified")
        print(f"Potential Additional Savings: ${impact.get('potential_cost_savings', 0):,.2f}")
        top_priority = impact.get('top_priority', 'None identified')
        print(f"Priority Action: {top_priority}")
        print("="*60 + "\n")
        
        # Save outputs
        print(f"Saving review output to: {args.output}")
        results_df.to_csv(args.output, index=False)
        
        if args.audit_output:
            print(f"Saving audit output to: {args.audit_output}")
            audit_df.to_csv(args.audit_output, index=False)
        
        # ELITE: Save analytics
        if args.analytics_output:
            print(f"Saving analytics to: {args.analytics_output}")
            import json
            with open(args.analytics_output, 'w') as f:
                json.dump(exec_summary, f, indent=2, default=str)
        
        # ELITE: Save auto-generated suggestions
        if args.suggestions_output:
            print(f"Saving AI suggestions to: {args.suggestions_output}")
            suggestions_df = pd.DataFrame(auto_suggestions)
            suggestions_df.to_csv(args.suggestions_output, index=False)
            
            # Also save Google Ads import format
            ads_format = auto_neg.export_to_ads_format()
            ads_file = args.suggestions_output.replace('.csv', '_ads_import.csv')
            with open(ads_file, 'w') as f:
                f.write(ads_format)
            print(f"Saved Google Ads import format to: {ads_file}")
        
        if args.analyze_output:
            print(f"Saving analysis output to: {args.analyze_output}")
            results_df.to_csv(args.analyze_output, index=False)
        
        print("Done. Elite processing complete.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
