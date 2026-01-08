import re

def normalize(text: str) -> str:
    """
    Normalizes a search term or negative keyword.
    1. Lowercase
    2. Trim whitespace
    3. Collapse multiple spaces
    4. Remove surrounding quotes/brackets
    """
    if not isinstance(text, str):
        return ""
    
    text = text.lower().strip()
    
    # Remove surrounding quotes (single or double) on the whole string
    # e.g., "running shoes" -> running shoes
    if text.startswith('"') and text.endswith('"') and len(text) > 1:
        text = text[1:-1]
    elif text.startswith("'") and text.endswith("'") and len(text) > 1:
        text = text[1:-1]
    elif text.startswith("[") and text.endswith("]") and len(text) > 1:
        text = text[1:-1]
        
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def tokenize(text: str) -> list[str]:
    """
    Splits text by space into tokens.
    """
    return text.split()

def is_exact_match(search_tokens: list[str], negative_tokens: list[str]) -> bool:
    """
    Checks for exact match: token lists must be identical.
    """
    return search_tokens == negative_tokens

def is_phrase_match(search_tokens: list[str], negative_tokens: list[str]) -> bool:
    """
    Checks for phrase match: negative_tokens must appear as a contiguous sub-sequence
    in search_tokens.
    """
    n_len = len(negative_tokens)
    s_len = len(search_tokens)
    
    if n_len > s_len:
        return False
    
    for i in range(s_len - n_len + 1):
        if search_tokens[i : i + n_len] == negative_tokens:
            return True
            
    return False

def is_broad_match(search_tokens: list[str], negative_tokens: list[str]) -> bool:
    """
    Checks for broad match: all tokens in negative_tokens must exist in search_tokens.
    Order does not matter.
    """
    # Using set containment
    search_set = set(search_tokens)
    negative_set = set(negative_tokens)
    return negative_set.issubset(search_set)

class Matcher:
    def __init__(self, negatives_df):
        self.exact_negatives = []
        self.phrase_negatives = []
        self.broad_negatives = []
        
        self._preprocess_negatives(negatives_df)

    def _preprocess_negatives(self, df):
        for _, row in df.iterrows():
            raw_keyword = row['negative_keyword']
            match_type = row['match_type']
            
            normalized = normalize(raw_keyword)
            tokens = tokenize(normalized)
            
            if not tokens: # Skip empty
                continue
                
            entry = {
                'original': raw_keyword,
                'tokens': tokens,
                'match_type': match_type
            }

            if match_type == 'EXACT':
                self.exact_negatives.append(entry)
            elif match_type == 'PHRASE':
                self.phrase_negatives.append(entry)
            elif match_type == 'BROAD':
                self.broad_negatives.append(entry)

    def match(self, search_term: str):
        """
        Checks if a search term is excluded.
        Returns (is_excluded, reason)
        """
        normalized_term = normalize(search_term)
        term_tokens = tokenize(normalized_term)
        
        if not term_tokens:
            return False, None

        # 1. Exact Match
        for neg in self.exact_negatives:
            if is_exact_match(term_tokens, neg['tokens']):
                return True, f"Excluded by EXACT negative: {neg['original']}"

        # 2. Phrase Match
        for neg in self.phrase_negatives:
            # Optimization: could check if all tokens are present first (broad check) before order check?
            # But phrase usually assumes simpler check. 
            # Optimization: Quick length check is already in `is_phrase_match`.
            if is_phrase_match(term_tokens, neg['tokens']):
                return True, f"Excluded by PHRASE negative: {neg['original']}"

        # 3. Broad Match
        for neg in self.broad_negatives:
            if is_broad_match(term_tokens, neg['tokens']):
                return True, f"Excluded by BROAD negative: {neg['original']}"

        return False, None
