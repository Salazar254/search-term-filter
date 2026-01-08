from collections import defaultdict
from matcher import tokenize, normalize, Matcher

def generate_ngrams(tokens: list[str], n: int) -> list[str]:
    """
    Generates n-grams from a list of tokens.
    """
    if len(tokens) < n:
        return []
    return [" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]

def analyze_search_terms(terms_df, negatives_df, max_n=3):
    """
    Analyzes non-excluded search terms to find frequent N-grams.
    Returns a DataFrame of N-gram statistics.
    """
    matcher = Matcher(negatives_df)
    
    # Dictionary to store stats: ngram -> {'count': 0, 'clicks': 0, 'cost': 0.0, 'impressions': 0}
    stats = defaultdict(lambda: {'count': 0, 'clicks': 0, 'cost': 0.0, 'impressions': 0})
    
    # Pre-calculate column indices/names for speed or just use standard iteration
    # Check if optional columns exist
    has_clicks = 'Clicks' in terms_df.columns
    has_cost = 'Cost' in terms_df.columns
    has_imps = 'Impressions' in terms_df.columns
    
    for _, row in terms_df.iterrows():
        term = str(row.get('Search term', ''))
        
        # 1. Check if excluded logic? 
        # The requirements say "Output only search terms that are NOT excluded... so a marketer can review".
        # Phase 2 goal: "Suggest 'new negatives' based on patterns"
        # Usually we only want to analyze patterns in the *remaining* (non-excluded) terms.
        # But maybe we want to analyze *all* terms to find patterns even if partially excluded?
        # Let's assume we analyze ONLY non-excluded terms to find *new* negatives.
        
        is_excluded, _ = matcher.match(term)
        if is_excluded:
            continue
            
        # 2. Normalize & Tokenize
        normalized = normalize(term)
        tokens = tokenize(normalized)
        
        if not tokens:
            continue
            
        # Get metrics
        clicks = pd_safe_numeric(row.get('Clicks', 0)) if has_clicks else 0
        cost = pd_safe_numeric(row.get('Cost', 0.0)) if has_cost else 0.0
        imps = pd_safe_numeric(row.get('Impressions', 0)) if has_imps else 0
        
        # 3. Generate N-Grams (1 to max_n)
        unique_ngrams_in_term = set()
        for n in range(1, max_n + 1):
            grams = generate_ngrams(tokens, n)
            for gram in grams:
                unique_ngrams_in_term.add(gram)
        
        # 4. Aggregate
        # Note: If a term has "running shoes", and we count "shoes" and "running", 
        # we are aggregating the metrics of the *whole search term* to the *ngram*.
        # This is standard behavior for N-Gram scripts (WordNgram script).
        for gram in unique_ngrams_in_term:
            s = stats[gram]
            s['count'] += 1
            s['clicks'] += clicks
            s['cost'] += cost
            s['impressions'] += imps

    # Convert to DataFrame
    data = []
    for gram, s in stats.items():
        data.append({
            'N-Gram': gram,
            'Word Count': len(gram.split()),
            'Occurrence Count': s['count'],
            'Clicks': s['clicks'],
            'Cost': s['cost'],
            'Impressions': s['impressions']
        })
        
    if not data:
        return None
        
    import pandas as pd
    result_df = pd.DataFrame(data)
    
    # Sort by Occurrence Count desc (or maybe Cost?)
    # usually Spend/Cost or Count is best
    result_df = result_df.sort_values(by='Occurrence Count', ascending=False)
    
    return result_df

def pd_safe_numeric(val):
    """Safely converts pandas value to number"""
    try:
        if isinstance(val, str):
            val = val.replace(',', '') # handle "1,000"
        return float(val)
    except:
        return 0.0
