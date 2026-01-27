import { useState } from 'react';

// Get API endpoint - works in both dev and production
const API_ENDPOINT = (() => {
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    // Development mode - using dev server
    return 'http://localhost:3001/api';
  }
  // Production mode (Electron app) - backend runs on localhost:3001
  return 'http://localhost:3001/api';
})();

const FILE_ENDPOINT = (() => {
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    return 'http://localhost:3001';
  }
  return 'http://localhost:3001';
})();

function App() {
    const [termsFile, setTermsFile] = useState<File | null>(null);
    const [negativesFile, setNegativesFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    const handleProcess = async () => {
        if (!termsFile || !negativesFile) {
            setError("Please select both files to proceed.");
            return;
        }

        setLoading(true);
        setError(null);
        setResults(null);

        const formData = new FormData();
        formData.append('terms', termsFile);
        formData.append('negatives', negativesFile);

        try {
            const response = await fetch(`${API_ENDPOINT}/upload-and-process`, {
                method: 'POST',
                body: formData,
                headers: {
                    'x-api-key': 'dev-key-change-in-production'
                }
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || 'Processing failed');
            }

            const data = await response.json();
            setResults(data);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-12 px-4 font-sans">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="text-center mb-12">
                    <h1 className="text-5xl font-bold text-white mb-3 tracking-tight">Search Term Filter</h1>
                    <p className="text-slate-300 text-lg">Optimize your Google Ads campaigns by filtering search terms against negative keywords</p>
                </div>

                {/* Main Card */}
                <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
                    <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-8">
                        <h2 className="text-2xl font-bold text-white">Upload Your Files</h2>
                        <p className="text-blue-100 mt-1">Select CSV or Excel files to begin filtering</p>
                    </div>

                    <div className="p-10 space-y-8">
                        {/* File Upload Section */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            {/* Search Terms Upload */}
                            <div className="relative group">
                                <label className="block text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                                    <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                                    </svg>
                                    Search Terms (CSV/XLSX)
                                </label>
                                <div className={`border-2 border-dashed rounded-xl p-8 transition-all duration-200 flex flex-col items-center justify-center cursor-pointer ${
                                    termsFile 
                                        ? 'border-green-400 bg-green-50' 
                                        : 'border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50'
                                }`}>
                                    <input
                                        type="file"
                                        accept=".csv, .xlsx"
                                        onChange={(e) => setTermsFile(e.target.files ? e.target.files[0] : null)}
                                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                    />
                                    {termsFile ? (
                                        <div className="text-center">
                                            <div className="text-4xl mb-2">✓</div>
                                            <p className="text-sm font-semibold text-gray-900">{termsFile.name}</p>
                                            <p className="text-xs text-gray-600 mt-1">{(termsFile.size / 1024).toFixed(2)} KB</p>
                                        </div>
                                    ) : (
                                        <div className="text-center">
                                            <svg className="w-8 h-8 text-gray-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                            </svg>
                                            <p className="text-sm font-semibold text-gray-700">Click or drag to upload</p>
                                            <p className="text-xs text-gray-500 mt-1">CSV or Excel file</p>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Negative Keywords Upload */}
                            <div className="relative group">
                                <label className="block text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                                    <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                                    </svg>
                                    Negative Keywords (CSV/XLSX)
                                </label>
                                <div className={`border-2 border-dashed rounded-xl p-8 transition-all duration-200 flex flex-col items-center justify-center cursor-pointer ${
                                    negativesFile 
                                        ? 'border-green-400 bg-green-50' 
                                        : 'border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50'
                                }`}>
                                    <input
                                        type="file"
                                        accept=".csv, .xlsx"
                                        onChange={(e) => setNegativesFile(e.target.files ? e.target.files[0] : null)}
                                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                    />
                                    {negativesFile ? (
                                        <div className="text-center">
                                            <div className="text-4xl mb-2">✓</div>
                                            <p className="text-sm font-semibold text-gray-900">{negativesFile.name}</p>
                                            <p className="text-xs text-gray-600 mt-1">{(negativesFile.size / 1024).toFixed(2)} KB</p>
                                        </div>
                                    ) : (
                                        <div className="text-center">
                                            <svg className="w-8 h-8 text-gray-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                            </svg>
                                            <p className="text-sm font-semibold text-gray-700">Click or drag to upload</p>
                                            <p className="text-xs text-gray-500 mt-1">CSV or Excel file</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Action Button */}
                        <div className="flex justify-center pt-4">
                            <button
                                onClick={handleProcess}
                                disabled={loading || !termsFile || !negativesFile}
                                className={`px-10 py-3 rounded-lg font-semibold text-white transition-all duration-200 transform ${
                                    loading || !termsFile || !negativesFile
                                        ? 'bg-gray-400 cursor-not-allowed' 
                                        : 'bg-blue-600 hover:bg-blue-700 active:scale-95 shadow-lg hover:shadow-xl'
                                }`}
                            >
                                {loading ? (
                                    <div className="flex items-center gap-2">
                                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                                        Processing...
                                    </div>
                                ) : (
                                    'Process Files'
                                )}
                            </button>
                        </div>

                        {/* Error Message */}
                        {error && (
                            <div className="bg-red-50 border-l-4 border-red-500 rounded-lg p-4 flex gap-3">
                                <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                </svg>
                                <div>
                                    <h3 className="font-semibold text-red-900">Error</h3>
                                    <p className="text-red-700 text-sm mt-1">{error}</p>
                                </div>
                            </div>
                        )}

                        {/* Results Area - Google Analytics Style Dashboard */}
                        {results && (
                            <div className="pt-8">
                                {/* Dashboard Header */}
                                <div className="mb-8">
                                    <h2 className="text-3xl font-bold text-gray-900">Campaign Analysis</h2>
                                    <p className="text-gray-500 text-sm mt-1">Real-time performance metrics and optimization insights</p>
                                </div>

                                {/* Key Metrics Row */}
                                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                                    <AnalyticsMetric 
                                        label="Cost Saved"
                                        value={`$${results.metrics?.cost_waste_prevented ? Number(results.metrics.cost_waste_prevented).toLocaleString('en-US', {maximumFractionDigits: 0}) : '0'}`}
                                        change={`${results.metrics?.cost_reduction_percentage || 0}% reduction`}
                                        color="text-blue-600"
                                    />
                                    <AnalyticsMetric 
                                        label="Quality Score"
                                        value={`${results.metrics?.quality_score || 0}%`}
                                        change="Campaign focus"
                                        color="text-green-600"
                                    />
                                    <AnalyticsMetric 
                                        label="Terms Excluded"
                                        value={results.terms_excluded || 0}
                                        change={`of ${results.total_terms_analyzed || 0} total`}
                                        color="text-orange-600"
                                    />
                                    <AnalyticsMetric 
                                        label="Action Score"
                                        value={`${results.metrics?.action_score || 0}`}
                                        change="out of 100"
                                        color="text-purple-600"
                                    />
                                </div>

                                {/* Main Analytics Grid */}
                                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                                    {/* Performance Overview */}
                                    <div className="lg:col-span-2 bg-white border border-gray-200 rounded-lg p-6">
                                        <div className="mb-6">
                                            <h3 className="text-lg font-semibold text-gray-900">Performance Overview</h3>
                                            <p className="text-gray-500 text-sm mt-1">Terms analysis and filtering results</p>
                                        </div>
                                        
                                        <div className="space-y-6">
                                            {/* Bars showing distribution */}
                                            <div>
                                                <div className="flex justify-between mb-2">
                                                    <span className="text-sm font-medium text-gray-700">Total Terms</span>
                                                    <span className="text-sm font-semibold text-gray-900">{results.total_terms_analyzed || 0}</span>
                                                </div>
                                                <div className="w-full bg-gray-200 rounded-full h-2"></div>
                                            </div>

                                            <div>
                                                <div className="flex justify-between mb-2">
                                                    <span className="text-sm font-medium text-gray-700">Excluded (Low Quality)</span>
                                                    <span className="text-sm font-semibold text-red-600">{results.terms_excluded || 0}</span>
                                                </div>
                                                <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                                                    <div 
                                                        className="bg-red-500 h-full rounded-full" 
                                                        style={{width: `${(results.terms_excluded / results.total_terms_analyzed * 100) || 0}%`}}
                                                    ></div>
                                                </div>
                                            </div>

                                            <div>
                                                <div className="flex justify-between mb-2">
                                                    <span className="text-sm font-medium text-gray-700">Remaining (Quality Terms)</span>
                                                    <span className="text-sm font-semibold text-green-600">{results.terms_remaining || 0}</span>
                                                </div>
                                                <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                                                    <div 
                                                        className="bg-green-500 h-full rounded-full" 
                                                        style={{width: `${(results.terms_remaining / results.total_terms_analyzed * 100) || 0}%`}}
                                                    ></div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Summary Stats */}
                                    <div className="bg-white border border-gray-200 rounded-lg p-6">
                                        <h3 className="text-lg font-semibold text-gray-900 mb-6">Summary</h3>
                                        
                                        <div className="space-y-4">
                                            <div className="flex items-center justify-between p-3 bg-blue-50 rounded">
                                                <span className="text-gray-700 text-sm">Conversion Rate</span>
                                                <span className="font-semibold text-blue-600">
                                                    {results.metrics?.quality_score ? `${results.metrics.quality_score.toFixed(1)}%` : '0%'}
                                                </span>
                                            </div>

                                            <div className="flex items-center justify-between p-3 bg-green-50 rounded">
                                                <span className="text-gray-700 text-sm">Cost Efficiency</span>
                                                <span className="font-semibold text-green-600">Good</span>
                                            </div>

                                            <div className="flex items-center justify-between p-3 bg-purple-50 rounded">
                                                <span className="text-gray-700 text-sm">Optimization</span>
                                                <span className="font-semibold text-purple-600">
                                                    {results.metrics?.action_score > 60 ? 'Recommended' : 'On Track'}
                                                </span>
                                            </div>

                                            <div className="flex items-center justify-between p-3 bg-orange-50 rounded">
                                                <span className="text-gray-700 text-sm">Total Savings</span>
                                                <span className="font-semibold text-orange-600">
                                                    ${results.metrics?.cost_waste_prevented ? Number(results.metrics.cost_waste_prevented).toLocaleString('en-US', {maximumFractionDigits: 0}) : '0'}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Insights Section */}
                                {results.recommendations && results.recommendations.length > 0 && (
                                    <div className="bg-white border border-gray-200 rounded-lg p-6 mb-8">
                                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Insights & Recommendations</h3>
                                        <div className="space-y-3">
                                            {results.recommendations.map((rec: string, idx: number) => (
                                                <div key={idx} className="flex gap-3 p-3 bg-blue-50 rounded-lg border border-blue-100">
                                                    <div className="text-blue-600 font-bold text-lg">💡</div>
                                                    <p className="text-gray-700 text-sm">{rec}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* High Risk Alert */}
                                {results.metrics?.high_risk_terms && results.metrics.high_risk_terms.length > 0 && (
                                    <div className="bg-white border border-red-200 rounded-lg p-6 mb-8">
                                        <div className="flex items-center gap-2 mb-4">
                                            <h3 className="text-lg font-semibold text-gray-900">High-Risk Terms</h3>
                                            <span className="bg-red-100 text-red-700 text-xs font-bold px-2 py-1 rounded">{results.metrics.high_risk_terms.length}</span>
                                        </div>
                                        <div className="overflow-x-auto">
                                            <table className="w-full text-sm">
                                                <thead>
                                                    <tr className="border-b border-gray-200">
                                                        <th className="text-left py-2 px-3 font-medium text-gray-700">Term</th>
                                                        <th className="text-right py-2 px-3 font-medium text-gray-700">Impressions</th>
                                                        <th className="text-right py-2 px-3 font-medium text-gray-700">Clicks</th>
                                                        <th className="text-right py-2 px-3 font-medium text-gray-700">Status</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {results.metrics.high_risk_terms.slice(0, 5).map((term: any, idx: number) => (
                                                        <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                                                            <td className="py-2 px-3 text-gray-900 font-medium">{term.term}</td>
                                                            <td className="text-right py-2 px-3 text-gray-600">{term.impressions}</td>
                                                            <td className="text-right py-2 px-3 text-gray-600">{term.clicks}</td>
                                                            <td className="text-right py-2 px-3">
                                                                <span className="bg-red-100 text-red-700 text-xs font-bold px-2 py-1 rounded">{term.risk_level}</span>
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                )}

                                {/* Download Section */}
                                <div className="bg-white border border-gray-200 rounded-lg p-6">
                                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Export Data</h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                                        <a href={`${FILE_ENDPOINT}${results.results.review}`} download className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition">
                                            <p className="font-medium text-gray-900 text-sm">Review File</p>
                                            <p className="text-gray-600 text-xs mt-1">CSV • Filtered terms</p>
                                        </a>
                                        <a href={`${FILE_ENDPOINT}${results.results.audit}`} download className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition">
                                            <p className="font-medium text-gray-900 text-sm">Audit Trail</p>
                                            <p className="text-gray-600 text-xs mt-1">CSV • Complete data</p>
                                        </a>
                                        <a href={`${FILE_ENDPOINT}${results.results.suggestions || results.results.analysis}`} download className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition">
                                            <p className="font-medium text-gray-900 text-sm">AI Suggestions</p>
                                            <p className="text-gray-600 text-xs mt-1">CSV • Negatives</p>
                                        </a>
                                        <a href={`${FILE_ENDPOINT}${results.results.analytics || results.results.editor}`} download className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition">
                                            <p className="font-medium text-gray-900 text-sm">Analytics</p>
                                            <p className="text-gray-600 text-xs mt-1">JSON • Full metrics</p>
                                        </a>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

function AnalyticsMetric({ label, value, change, color }: { label: string, value: string | number, change: string, color: string }) {
    return (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
            <p className="text-gray-600 text-xs font-medium mb-2">{label}</p>
            <p className={`text-3xl font-bold ${color}`}>{value}</p>
            <p className="text-gray-500 text-xs mt-2">{change}</p>
        </div>
    );
}

export default App;
