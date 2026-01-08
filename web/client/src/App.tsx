import { useState } from 'react';

function App() {
    const [termsFile, setTermsFile] = useState<File | null>(null);
    const [negativesFile, setNegativesFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    const handleProcess = async () => {
        if (!termsFile || !negativesFile) {
            setError("Please select both files.");
            return;
        }

        setLoading(true);
        setError(null);
        setResults(null);

        const formData = new FormData();
        formData.append('terms', termsFile);
        formData.append('negatives', negativesFile);

        try {
            const response = await fetch('http://localhost:3001/api/upload-and-process', {
                method: 'POST',
                body: formData,
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
        <div className="min-h-screen bg-gray-100 py-10 px-5 font-sans">
            <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-lg overflow-hidden">
                <div className="bg-blue-600 p-6">
                    <h1 className="text-3xl font-bold text-white">Search Term Filter</h1>
                    <p className="text-blue-100 mt-2">Upload your Google Ads Search Terms and Negative Keywords to filter them.</p>
                </div>

                <div className="p-8 space-y-8">
                    {/* File Uploads */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 flex flex-col items-center justify-center bg-gray-50 hover:bg-gray-100 transition">
                            <label className="block text-gray-700 font-semibold mb-2">Search Terms (CSV/XLSX)</label>
                            <input
                                type="file"
                                accept=".csv, .xlsx"
                                onChange={(e) => setTermsFile(e.target.files ? e.target.files[0] : null)}
                                className="block w-full text-sm text-slate-500
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-full file:border-0
                  file:text-sm file:font-semibold
                  file:bg-blue-50 file:text-blue-700
                  hover:file:bg-blue-100
                "
                            />
                            {termsFile && <p className="mt-2 text-sm text-green-600 font-medium">{termsFile.name}</p>}
                        </div>

                        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 flex flex-col items-center justify-center bg-gray-50 hover:bg-gray-100 transition">
                            <label className="block text-gray-700 font-semibold mb-2">Negative Keywords (CSV/XLSX)</label>
                            <input
                                type="file"
                                accept=".csv, .xlsx"
                                onChange={(e) => setNegativesFile(e.target.files ? e.target.files[0] : null)}
                                className="block w-full text-sm text-slate-500
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-full file:border-0
                  file:text-sm file:font-semibold
                  file:bg-blue-50 file:text-blue-700
                  hover:file:bg-blue-100
                "
                            />
                            {negativesFile && <p className="mt-2 text-sm text-green-600 font-medium">{negativesFile.name}</p>}
                        </div>
                    </div>

                    {/* Action Button */}
                    <div className="flex justify-center">
                        <button
                            onClick={handleProcess}
                            disabled={loading}
                            className={`px-8 py-3 rounded-lg text-white font-bold text-lg shadow-md transition transform hover:-translate-y-1 ${loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
                                }`}
                        >
                            {loading ? 'Processing...' : 'Process Files'}
                        </button>
                    </div>

                    {/* Error Message */}
                    {error && (
                        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded">
                            <p className="text-red-700">{error}</p>
                        </div>
                    )}

                    {/* Results Area */}
                    {results && (
                        <div className="animate-fade-in-up">
                            <h2 className="text-2xl font-bold text-gray-800 mb-4">Results Ready</h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                <ResultCard
                                    title="Review File"
                                    desc="Filtered terms for manual review"
                                    link={`http://localhost:3001${results.results.review}`}
                                    color="bg-green-100 text-green-800"
                                />
                                <ResultCard
                                    title="Audit File"
                                    desc="All terms with exclusion status"
                                    link={`http://localhost:3001${results.results.audit}`}
                                    color="bg-yellow-100 text-yellow-800"
                                />
                                <ResultCard
                                    title="N-Gram Analysis"
                                    desc="New negative keyword ideas"
                                    link={`http://localhost:3001${results.results.analysis}`}
                                    color="bg-purple-100 text-purple-800"
                                />
                                <ResultCard
                                    title="Editor Export"
                                    desc="Ready for Google Ads Editor"
                                    link={`http://localhost:3001${results.results.editor}`}
                                    color="bg-indigo-100 text-indigo-800"
                                />
                            </div>

                            <div className="mt-6 bg-gray-900 text-gray-300 p-4 rounded-lg overflow-x-auto text-sm font-mono">
                                <h3 className="text-white font-bold mb-2">Processing Logs</h3>
                                <pre>{results.logs}</pre>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function ResultCard({ title, desc, link, color }: { title: string, desc: string, link: string, color: string }) {
    return (
        <a href={link} download className={`block p-4 rounded-lg shadow transition hover:shadow-md ${color} hover:opacity-90`}>
            <h3 className="font-bold text-lg">{title}</h3>
            <p className="text-sm opacity-80 mb-3">{desc}</p>
            <span className="inline-block bg-white bg-opacity-30 px-3 py-1 rounded text-xs font-bold uppercase tracking-wide">Download</span>
        </a>
    );
}

export default App;
