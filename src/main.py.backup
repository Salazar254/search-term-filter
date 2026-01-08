import argparse
import sys
import pandas as pd
from datetime import datetime
from data_loader import load_search_terms, load_negatives
from matcher import Matcher
from analysis import analyze_search_terms

def main():
    parser = argparse.ArgumentParser(description="Filter Google Ads Search Terms against Negative Keywords.")
    parser.add_argument('--terms', required=True, help="Path to Search Terms file (CSV/XLSX)")
    parser.add_argument('--negatives', required=True, help="Path to Negative Keywords file (CSV/XLSX)")
    parser.add_argument('--output', required=True, help="Path to output file for manual review (CSV/XLSX)")
    parser.add_argument('--audit-output', help="Optional path to audit output file (all terms with status)")
    parser.add_argument('--analyze-output', help="Optional path to N-Gram analysis output file")
    parser.add_argument('--editor-export', help="Optional path to Google Ads Editor export file (adds terms as Negative Exact)")
    
    args = parser.parse_args()
    
    print(f"Loading search terms from: {args.terms}")
    try:
        terms_df = load_search_terms(args.terms)
    except Exception as e:
        print(f"Error loading search terms: {e}")
        sys.exit(1)
        
    print(f"Loading negatives from: {args.negatives}")
    try:
        negatives_df = load_negatives(args.negatives)
    except Exception as e:
        print(f"Error loading negatives: {e}")
        sys.exit(1)
        
    print(f"Loaded {len(terms_df)} search terms and {len(negatives_df)} negatives.")
    
    matcher = Matcher(negatives_df)
    
    print("Filtering terms...")
    
    results = []
    
    # We need to preserve original columns
    # We'll iterate and build a list of dicts to create a new DF safely
    
    # Convert terms_df to list of records for iteration
    terms_records = terms_df.to_dict('records')
    
    review_rows = []
    audit_rows = []
    
    excluded_count = 0
    
    for row in terms_records:
        term = row.get('Search term', '')
        # Handle non-string terms (e.g. NaN) gracefully?
        if pd.isna(term):
            term = ""
            
        is_excluded, reason = matcher.match(str(term))
        
        # Prepare row data
        row_data = row.copy()
        row_data['excluded_by_negatives'] = is_excluded
        row_data['exclusion_reason'] = reason if reason else "Not matched by any negative"
        row_data['checked_at'] = datetime.now().isoformat()
        
        # For Audit file
        if args.audit_output:
            # Parse reason for specific columns if we want strict schema
            # reason is like "Excluded by MATCH_TYPE negative: KEYWORD"
            match_type = None
            keyword = None
            if is_excluded and reason.startswith("Excluded by"):
                parts = reason.split(" negative: ", 1)
                if len(parts) == 2:
                    # parts[0] is "Excluded by TYPE"
                    match_type_part = parts[0].replace("Excluded by ", "")
                    match_type = match_type_part
                    keyword = parts[1]
            
            audit_row = row_data.copy()
            audit_row['matched_negative_keyword'] = keyword
            audit_row['matched_negative_match_type'] = match_type
            audit_rows.append(audit_row)
        
        if is_excluded:
            excluded_count += 1
        else:
            # For review file, only include non-excluded
             review_rows.append(row_data)
             
    print(f"Filtering complete. Excluded {excluded_count} terms. Remaining {len(review_rows)} terms.")
    
    # Save Review Output
    print(f"Saving review output to: {args.output}")
    if review_rows:
        review_df = pd.DataFrame(review_rows)
    else:
        # Empty result, keep structure
        review_df = pd.DataFrame(columns=terms_df.columns.tolist() + ['excluded_by_negatives', 'exclusion_reason', 'checked_at'])
        
    if args.output.lower().endswith('.csv'):
        review_df.to_csv(args.output, index=False)
    elif args.output.lower().endswith('.xlsx'):
        review_df.to_excel(args.output, index=False)
        
    # Save Audit Output
    if args.audit_output:
        print(f"Saving audit output to: {args.audit_output}")
        if audit_rows:
            audit_df = pd.DataFrame(audit_rows)
        else:
            audit_df = pd.DataFrame(columns=terms_df.columns.tolist() + ['matched_negative_keyword', 'matched_negative_match_type'])
            
        if args.audit_output.lower().endswith('.csv'):
            audit_df.to_csv(args.audit_output, index=False)
        elif args.audit_output.lower().endswith('.xlsx'):
            audit_df.to_excel(args.audit_output, index=False)

    # N-Gram Analysis
    if args.analyze_output:
        print("Running N-Gram Analysis...")
        analysis_df = analyze_search_terms(terms_df, negatives_df)
        
        print(f"Saving analysis output to: {args.analyze_output}")
        if analysis_df is not None and not analysis_df.empty:
            if args.analyze_output.lower().endswith('.csv'):
                analysis_df.to_csv(args.analyze_output, index=False)
            elif args.analyze_output.lower().endswith('.xlsx'):
                analysis_df.to_excel(args.analyze_output, index=False)
        else:
            print("No data for analysis (or no non-excluded terms).")

    # Google Ads Editor Export
    if args.editor_export and review_rows:
        print(f"Saving Editor Export to: {args.editor_export}")
        # Columns: Campaign, Ad Group, Keyword, Criterion Type
        editor_rows = []
        for row in review_rows:
            # Only include if Campaign/Ad Group columns exist?
            # User requirement says optional columns preserved. 
            # If Campaign/Ad Group are missing, Editor import might fail or require user to select manually.
            # We'll map what we have.
            
            camp = row.get('Campaign', '')
            adg = row.get('Ad group', '')
            term = row.get('Search term', '')
            
            editor_rows.append({
                'Campaign': camp,
                'Ad Group': adg,
                'Keyword': term,
                'Criterion Type': 'Negative Exact' # Defaulting to Exact
            })
            
        editor_df = pd.DataFrame(editor_rows)
        if args.editor_export.lower().endswith('.csv'):
            editor_df.to_csv(args.editor_export, index=False)
        elif args.editor_export.lower().endswith('.xlsx'):
            editor_df.to_excel(args.editor_export, index=False)
    elif args.editor_export:
        print("No terms to export for Editor.")

    print("Done.")

if __name__ == "__main__":
    main()
