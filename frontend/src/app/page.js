'use client';

import { useState, useEffect } from 'react';
import SearchBar from '@/components/SearchBar';
// import SearchResults from '@/components/SearchResults';
// import IndexingPanel from '@/components/IndexingPanel';
import { searchFiles, checkHealth } from '@/lib/api';

export default function Home() {
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [currentQuery, setCurrentQuery] = useState('');
  const [showIndexing, setShowIndexing] = useState(false);
  const [backendStatus, setBackendStatus] = useState('checking');

  // Check backend health on mount
  useEffect(() => {
    const checkBackend = async () => {
      try {
        await checkHealth();
        setBackendStatus('connected');
      } catch (err) {
        setBackendStatus('disconnected');
      }
    };
    checkBackend();
  }, []);

  const handleSearch = async (query) => {
    setIsSearching(true);
    setCurrentQuery(query);
    
    try {
      const data = await searchFiles(query, 10);
      setResults(data.results);
    } catch (error) {
      console.error('Search failed:', error);
      alert('Search failed. Make sure the backend is running.');
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                🔍 AI File Search
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                Semantic search powered by local AI
              </p>
            </div>
            <div className="flex items-center gap-4">
              {/* Backend Status */}
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${
                  backendStatus === 'connected' ? 'bg-green-500' : 
                  backendStatus === 'disconnected' ? 'bg-red-500' : 
                  'bg-yellow-500'
                }`} />
                <span className="text-sm text-gray-600">
                  {backendStatus === 'connected' ? 'Connected' : 
                   backendStatus === 'disconnected' ? 'Disconnected' : 
                   'Checking...'}
                </span>
              </div>
              
              {/* Toggle Indexing Panel */}
              <button
                onClick={() => setShowIndexing(!showIndexing)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
              >
                {showIndexing ? 'Hide' : 'Show'} Indexing
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Search */}
          <div className="lg:col-span-2 space-y-6">
            {/* Search Bar */}
            <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
              <SearchBar onSearch={handleSearch} isLoading={isSearching} />
            </div>

            {/* Search Results */}
            {isSearching ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
                  <p className="text-gray-600">Searching your files...</p>
                </div>
              </div>
            ) : (
              //<SearchResults results={results} query={currentQuery} />
            )}
          </div>

          {/* Right Column - Indexing Panel */}
          <div className="lg:col-span-1">
            {showIndexing && <IndexingPanel />}
            
            {/* Info Card */}
            {!showIndexing && (
              <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-800 mb-3">
                  How to Use
                </h3>
                <ol className="text-sm text-gray-600 space-y-2 list-decimal list-inside">
                  <li>Click &quot;Show Indexing&quot; to index your files</li>
                  <li>Enter a directory path (e.g., ~/Documents)</li>
                  <li>Wait for indexing to complete</li>
                  <li>Search using natural language queries</li>
                  <li>Click &quot;Open File&quot; to view results</li>
                </ol>
                
                <div className="mt-4 p-3 bg-blue-50 rounded-md border border-blue-200">
                  <p className="text-xs text-blue-800">
                    <strong>Example queries:</strong><br/>
                    • &quot;Python function definitions&quot;<br/>
                    • &quot;API documentation&quot;<br/>
                    • &quot;configuration settings&quot;<br/>
                    • &quot;error handling code&quot;
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8 text-center text-sm text-gray-500">
        <p>Powered by Ollama (nomic-embed-text) • FastAPI • Next.js</p>
      </footer>
    </div>
  );
}