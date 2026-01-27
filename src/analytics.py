"""
Elite Analytics Engine - Real-time ROI optimization metrics
Ruthlessly focuses on what matters: Money, Speed, Impact
"""
import pandas as pd
import numpy as np
from datetime import datetime
import json

class PerformanceAnalytics:
    """High-speed performance metrics for decision makers"""
    
    def __init__(self, terms_df, negatives_df, filtered_results_df):
        self.terms_df = terms_df
        self.negatives_df = negatives_df
        self.results_df = filtered_results_df
        self.metrics = {}
        
    def calculate_cost_savings(self):
        """Calculate immediate cost savings from exclusions"""
        # Get excluded terms with performance metrics
        excluded = self.results_df[self.results_df['excluded_by_negatives']]
        
        # Safely handle cost column
        if 'Cost' in excluded.columns:
            total_cost_waste = pd.to_numeric(excluded['Cost'], errors='coerce').sum()
        else:
            # Estimate from clicks if cost not available
            total_cost_waste = len(excluded) * 2.5  # Assume $2.50 avg cost
        
        self.metrics['cost_waste_prevented'] = round(total_cost_waste, 2)
        
        # Calculate for remaining terms
        remaining = self.results_df[~self.results_df['excluded_by_negatives']]
        if 'Cost' in remaining.columns:
            total_remaining_cost = pd.to_numeric(remaining['Cost'], errors='coerce').sum()
        else:
            total_remaining_cost = len(remaining) * 2.5
            
        self.metrics['total_remaining_spend'] = round(total_remaining_cost, 2)
        
        # ROI improvement potential
        if total_remaining_cost > 0:
            self.metrics['cost_reduction_percentage'] = round(
                (total_cost_waste / (total_cost_waste + total_remaining_cost)) * 100, 1
            )
        else:
            self.metrics['cost_reduction_percentage'] = 0
            
        return self.metrics
    
    def calculate_quality_metrics(self):
        """Calculate quality and efficiency scores"""
        excluded = self.results_df[self.results_df['excluded_by_negatives']]
        remaining = self.results_df[~self.results_df['excluded_by_negatives']]
        
        # Quality score: how focused is the remaining traffic
        total_terms = len(self.results_df)
        quality_ratio = len(remaining) / total_terms if total_terms > 0 else 0
        self.metrics['quality_score'] = round(quality_ratio * 100, 1)
        
        # Excluded term quality
        if len(excluded) > 0 and 'Clicks' in excluded.columns:
            avg_excluded_clicks = pd.to_numeric(excluded['Clicks'], errors='coerce').mean()
            self.metrics['avg_clicks_excluded_term'] = round(avg_excluded_clicks, 1)
        
        # Efficiency: impressions that will never waste budget
        if 'Impressions' in excluded.columns:
            waste_impressions = pd.to_numeric(excluded['Impressions'], errors='coerce').sum()
            self.metrics['impressions_eliminated'] = int(waste_impressions)
        
        return self.metrics
    
    def identify_high_risk_terms(self):
        """Identify terms that are draining budget without ROI"""
        remaining = self.results_df[~self.results_df['excluded_by_negatives']].copy()
        risk_terms = []
        
        if len(remaining) == 0:
            self.metrics['high_risk_terms'] = []
            return []
        
        # Terms with high impressions but low clicks (wasting impressions)
        remaining['click_through_rate'] = 0
        if 'Impressions' in remaining.columns and 'Clicks' in remaining.columns:
            imps = pd.to_numeric(remaining['Impressions'], errors='coerce')
            clicks = pd.to_numeric(remaining['Clicks'], errors='coerce')
            remaining['click_through_rate'] = (clicks / imps.clip(lower=1)) * 100
            
            # Flag terms with 0 CTR and high impressions
            low_performers = remaining[
                (remaining['click_through_rate'] == 0) & 
                (imps > imps.quantile(0.75))
            ]
            
            for idx, row in low_performers.iterrows():
                risk_terms.append({
                    'term': str(row['Search term']),
                    'impressions': int(row['Impressions']) if 'Impressions' in row else 0,
                    'clicks': int(row['Clicks']) if 'Clicks' in row else 0,
                    'risk_level': 'CRITICAL' if row['Impressions'] > imps.quantile(0.9) else 'HIGH'
                })
        
        self.metrics['high_risk_terms'] = sorted(risk_terms, 
                                                 key=lambda x: x['impressions'], 
                                                 reverse=True)[:10]
        return risk_terms
    
    def generate_recommendation_score(self):
        """Generate overall action score (0-100)"""
        score = 0
        
        # Cost savings potential (max 40 points)
        if self.metrics.get('cost_reduction_percentage', 0) > 20:
            score += 40
        elif self.metrics.get('cost_reduction_percentage', 0) > 10:
            score += 25
        else:
            score += 10
        
        # Quality improvement (max 30 points)
        quality = self.metrics.get('quality_score', 0)
        score += min(30, (quality / 100) * 30)
        
        # Risk mitigation (max 30 points)
        high_risk = len(self.metrics.get('high_risk_terms', []))
        if high_risk > 0:
            score += min(30, high_risk * 3)
        
        self.metrics['action_score'] = min(100, round(score, 0))
        return self.metrics['action_score']
    
    def get_executive_summary(self):
        """Generate one-page exec summary for decision makers"""
        self.calculate_cost_savings()
        self.calculate_quality_metrics()
        self.identify_high_risk_terms()
        self.generate_recommendation_score()
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_terms_analyzed': len(self.results_df),
            'terms_excluded': int(self.results_df['excluded_by_negatives'].sum()),
            'terms_remaining': int((~self.results_df['excluded_by_negatives']).sum()),
            'metrics': self.metrics,
            'action_required': self.metrics['action_score'] >= 60,
            'recommendation': self._generate_recommendation()
        }
        return summary
    
    def _generate_recommendation(self):
        """AI-generated action recommendation"""
        score = self.metrics.get('action_score', 0)
        cost_saved = self.metrics.get('cost_waste_prevented', 0)
        risk_terms = len(self.metrics.get('high_risk_terms', []))
        
        recommendations = []
        
        if cost_saved > 1000:
            recommendations.append(f"URGENT: ${cost_saved:,.0f} in preventable spend identified")
        
        if risk_terms > 5:
            recommendations.append(f"{risk_terms} terms actively draining budget - implement negatives immediately")
        
        if self.metrics.get('cost_reduction_percentage', 0) > 30:
            recommendations.append("Aggressive negative keyword implementation will significantly improve ROI")
        
        if not recommendations:
            recommendations.append("Continue current strategy - campaigns are well-optimized")
        
        return recommendations

