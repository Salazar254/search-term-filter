"""
Elite Batch Processor - Handle multiple campaigns in parallel with zero latency
Built for speed and scale, like a Tesla production line
"""
import os
import json
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

class EliteBatchProcessor:
    """Parallel campaign processing - enterprise scale"""
    
    def __init__(self, max_workers=8):
        self.max_workers = max_workers
        self.results = []
        
    def process_campaign(self, terms_file, negatives_file, campaign_name):
        """Process single campaign"""
        output_dir = Path("web/server/outputs")
        timestamp = int(datetime.now().timestamp() * 1000)
        
        output_file = output_dir / f"review-{campaign_name}-{timestamp}.csv"
        audit_file = output_dir / f"audit-{campaign_name}-{timestamp}.csv"
        analytics_file = output_dir / f"analytics-{campaign_name}-{timestamp}.json"
        suggestions_file = output_dir / f"suggestions-{campaign_name}-{timestamp}.csv"
        
        try:
            # Call main.py for this campaign
            cmd = [
                "python", "src/main.py",
                "--terms", terms_file,
                "--negatives", negatives_file,
                "--output", str(output_file),
                "--audit-output", str(audit_file),
                "--analytics-output", str(analytics_file),
                "--suggestions-output", str(suggestions_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            return {
                'campaign': campaign_name,
                'success': result.returncode == 0,
                'files': {
                    'review': str(output_file),
                    'audit': str(audit_file),
                    'analytics': str(analytics_file),
                    'suggestions': str(suggestions_file)
                },
                'error': result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {
                'campaign': campaign_name,
                'success': False,
                'error': str(e)
            }
    
    def process_batch(self, campaigns):
        """Process multiple campaigns in parallel
        
        Args:
            campaigns: List of {'name': str, 'terms': path, 'negatives': path}
        
        Returns:
            List of results with output files and metrics
        """
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self.process_campaign,
                    c['terms'],
                    c['negatives'],
                    c['name']
                ): c['name'] for c in campaigns
            }
            
            results = []
            for future in as_completed(futures):
                campaign = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    print(f"✓ {campaign} completed")
                except Exception as e:
                    print(f"✗ {campaign} failed: {e}")
                    results.append({
                        'campaign': campaign,
                        'success': False,
                        'error': str(e)
                    })
        
        return results
    
    def generate_batch_report(self, results):
        """Generate executive batch report"""
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_campaigns': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': f"{(len(successful)/len(results)*100):.1f}%" if results else "0%",
            'campaigns': results
        }
        
        print("\n" + "="*70)
        print("ELITE BATCH PROCESSING REPORT")
        print("="*70)
        print(f"Campaigns Processed: {len(results)}")
        print(f"Success Rate: {report['success_rate']}")
        print(f"Total Processing Time: {datetime.now().isoformat()}")
        print("="*70)
        
        return report

# Example usage
if __name__ == "__main__":
    processor = EliteBatchProcessor(max_workers=8)
    
    # Example: process multiple campaigns
    campaigns = [
        {
            'name': 'campaign_us_desktop',
            'terms': 'data/terms_us_desktop.csv',
            'negatives': 'data/negatives.csv'
        },
        {
            'name': 'campaign_us_mobile',
            'terms': 'data/terms_us_mobile.csv',
            'negatives': 'data/negatives.csv'
        },
        {
            'name': 'campaign_uk',
            'terms': 'data/terms_uk.csv',
            'negatives': 'data/negatives.csv'
        }
    ]
    
    # Process all campaigns in parallel
    results = processor.process_batch(campaigns)
    report = processor.generate_batch_report(results)
    
    # Save report
    with open('batch_report.json', 'w') as f:
        json.dump(report, f, indent=2)
