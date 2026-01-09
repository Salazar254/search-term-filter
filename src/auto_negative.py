"""
AutoNegative - AI-powered negative keyword discovery
Learns patterns from poor performers to autonomously suggest negatives
"""
import pandas as pd
import numpy as np
from collections import defaultdict
import re

class AutoNegativeEngine:
    """Intelligent negative keyword generation from performance data"""
    
    def __init__(self, terms_df):
        self.terms_df = terms_df.copy()
        self.suggested_negatives = []
        
    def analyze_poor_performers(self):
        """Find low-quality terms that should be negated"""
        # Safe column access
        if 'Clicks' not in self.terms_df.columns:
            self.terms_df['Clicks'] = 0
        if 'Impressions' not in self.terms_df.columns:
            self.terms_df['Impressions'] = 1
        if 'Cost' not in self.terms_df.columns:
            self.terms_df['Cost'] = 0
            
        # Convert to numeric
        self.terms_df['Clicks'] = pd.to_numeric(self.terms_df['Clicks'], errors='coerce').fillna(0)
        self.terms_df['Impressions'] = pd.to_numeric(self.terms_df['Impressions'], errors='coerce').fillna(1)
        self.terms_df['Cost'] = pd.to_numeric(self.terms_df['Cost'], errors='coerce').fillna(0)
        
        # Calculate metrics safely (prevent division by zero)
        self.terms_df['CTR'] = np.where(
            self.terms_df['Impressions'] > 0,
            (self.terms_df['Clicks'] / self.terms_df['Impressions']) * 100,
            0
        )
        self.terms_df['CPC'] = np.where(
            self.terms_df['Clicks'] > 0,
            self.terms_df['Cost'] / self.terms_df['Clicks'],
            0
        )
        
        # Identify poor performers (high impressions, zero clicks)
        poor = self.terms_df[
            (self.terms_df['CTR'] == 0) & 
            (self.terms_df['Impressions'] > 10)
        ]
        
        return poor
    
    def extract_keywords_from_terms(self, terms):
        """Break down terms into keyword components for pattern analysis"""
        all_keywords = defaultdict(lambda: {'count': 0, 'cost': 0, 'clicks': 0, 'imps': 0})
        
        for _, row in terms.iterrows():
            term = str(row['Search term']).lower().strip()
            words = re.findall(r'\b\w+\b', term)
            
            for word in words:
                all_keywords[word]['count'] += 1
                all_keywords[word]['cost'] += float(row.get('Cost', 0))
                all_keywords[word]['clicks'] += int(row.get('Clicks', 0))
                all_keywords[word]['imps'] += int(row.get('Impressions', 0))
        
        return all_keywords
    
    def calculate_confidence_score(self, keyword, keyword_stats, total_poor_performers):
        """Calculate confidence that this keyword should be excluded (0-100)"""
        score = 0
        
        # Occurrence frequency (up to 30 points)
        # Cap ratio at 1.0 to avoid exceeding max score
        max_ratio = min(1.0, keyword_stats['count'] / max(total_poor_performers, 1))
        score += max_ratio * 30
        
        # Zero-click rate (up to 40 points)
        if keyword_stats['imps'] > 0:
            zero_click_rate = 1 - (keyword_stats['clicks'] / keyword_stats['imps'])
            score += min(40, zero_click_rate * 40)
        
        # Cost per click (up to 30 points)
        if keyword_stats['clicks'] > 0:
            cpc = keyword_stats['cost'] / keyword_stats['clicks']
            if cpc > 5:  # High CPC indicates wasted spend
                score += 30
            elif cpc > 2:
                score += 15
        
        return min(100, score)
    
    def generate_suggestions(self, threshold=65):
        """Generate automatic negative keyword suggestions"""
        poor_performers = self.analyze_poor_performers()
        
        if len(poor_performers) == 0:
            return []
        
        # Extract keywords from poor performers
        poor_keywords = self.extract_keywords_from_terms(poor_performers)
        
        # Score each keyword
        suggestions = []
        for keyword, stats in poor_keywords.items():
            confidence = self.calculate_confidence_score(
                keyword, stats, len(poor_performers)
            )
            
            if confidence >= threshold:
                suggestions.append({
                    'keyword': keyword,
                    'confidence': round(confidence, 1),
                    'occurrences': stats['count'],
                    'zero_click_count': stats['imps'] - stats['clicks'],
                    'wasted_cost': round(stats['cost'], 2),
                    'match_type': 'BROAD',
                    'impact_rating': self._get_impact_rating(confidence, stats['cost'])
                })
        
        # Sort by impact
        self.suggested_negatives = sorted(
            suggestions, 
            key=lambda x: x['confidence'] * (x['wasted_cost'] + 1), 
            reverse=True
        )
        
        return self.suggested_negatives[:20]  # Return top 20
    
    def _get_impact_rating(self, confidence, cost):
        """Rate impact of this suggestion"""
        if confidence >= 85 and cost > 100:
            return "CRITICAL"
        elif confidence >= 75 and cost > 50:
            return "HIGH"
        elif confidence >= 65:
            return "MEDIUM"
        else:
            return "LOW"
    
    def export_to_ads_format(self):
        """Export suggestions in Google Ads Editor format"""
        if not self.suggested_negatives:
            return ""
        
        csv_lines = ["Keyword", "Match Type", "Negative"]
        for suggestion in self.suggested_negatives:
            csv_lines.append(f",-{suggestion['keyword']},EXACT")
        
        return "\n".join(csv_lines)
    
    def get_impact_summary(self):
        """Summarize potential savings from suggestions"""
        if not self.suggested_negatives:
            return {
                'total_suggested': 0,
                'potential_cost_savings': 0,
                'potential_impression_reduction': 0
            }
        
        total_cost = sum(s['wasted_cost'] for s in self.suggested_negatives)
        total_imps = sum(s['zero_click_count'] for s in self.suggested_negatives)
        
        return {
            'total_suggested': len(self.suggested_negatives),
            'potential_cost_savings': round(total_cost, 2),
            'potential_impression_reduction': int(total_imps),
            'top_priority': self.suggested_negatives[0]['keyword'] if self.suggested_negatives else None
        }

