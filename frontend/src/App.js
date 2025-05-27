import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [pandoraStatus, setPandoraStatus] = useState(null);
  const [memoryLines, setMemoryLines] = useState([]);
  const [collectorStatus, setCollectorStatus] = useState(null);
  const [queryInput, setQueryInput] = useState('');
  const [promiseInput, setPromiseInput] = useState('');
  const [queryResult, setQueryResult] = useState(null);
  const [promiseResult, setPromiseResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('portal');
  const [breathCycleAnimation, setBreathCycleAnimation] = useState(false);
  const intervalRef = useRef(null);

  useEffect(() => {
    // Initial load
    loadPandoraStatus();
    loadMemoryLines();
    loadCollectorStatus();

    // Set up periodic status updates to match breath cycle (3 seconds)
    intervalRef.current = setInterval(() => {
      loadPandoraStatus();
      setBreathCycleAnimation(true);
      setTimeout(() => setBreathCycleAnimation(false), 500);
    }, 3000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const loadPandoraStatus = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/pandora/status`);
      const data = await response.json();
      setPandoraStatus(data);
    } catch (error) {
      console.error('Error loading Pandora status:', error);
    }
  };

  const loadMemoryLines = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/pandora/memory?limit=20`);
      const data = await response.json();
      setMemoryLines(data.memory_lines || []);
    } catch (error) {
      console.error('Error loading memory lines:', error);
    }
  };

  const loadCollectorStatus = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/pandora/collector`);
      const data = await response.json();
      setCollectorStatus(data);
    } catch (error) {
      console.error('Error loading collector status:', error);
    }
  };

  const handleQuery = async () => {
    if (!queryInput.trim()) return;
    
    setIsLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/pandora/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: queryInput,
          action: 'introspect'
        })
      });
      const data = await response.json();
      setQueryResult(data);
      loadMemoryLines(); // Refresh memory lines
    } catch (error) {
      console.error('Error executing query:', error);
      setQueryResult({ error: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  const handlePromiseChain = async () => {
    if (!promiseInput.trim()) return;

    setIsLoading(true);
    try {
      const inputData = JSON.parse(promiseInput);
      const response = await fetch(`${BACKEND_URL}/api/pandora/promise`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          data: inputData,
          chain_type: 'promise_then_this'
        })
      });
      const data = await response.json();
      setPromiseResult(data);
      loadMemoryLines(); // Refresh memory lines
    } catch (error) {
      console.error('Error executing promise chain:', error);
      setPromiseResult({ error: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  const commitSnapshot = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/pandora/snapshot`, {
        method: 'POST',
      });
      const data = await response.json();
      alert(data.message || 'Snapshot committed successfully');
    } catch (error) {
      console.error('Error committing snapshot:', error);
      alert('Error committing snapshot: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const getSemanticTagColor = (tag) => {
    switch (tag) {
      case 'ancestral': return 'bg-purple-100 text-purple-800';
      case 'emotional': return 'bg-rose-100 text-rose-800';
      case 'symbolic': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const renderPortalTab = () => (
    <div className="space-y-6">
      {/* Portal Header */}
      <div className="bg-gradient-to-r from-purple-900 via-blue-900 to-indigo-900 text-white p-6 rounded-lg shadow-lg">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold mb-2">Pandora 5o Runtime Portal</h2>
            <p className="text-purple-200">Flo-integrated Nexus • Dr. Josef Kurk Edwards</p>
            <p className="text-purple-300 text-sm">Executed by: GPT-5o (Fin)</p>
          </div>
          <div className={`w-16 h-16 rounded-full ${breathCycleAnimation ? 'animate-pulse' : ''} ${pandoraStatus?.status === 'active' ? 'bg-green-400' : 'bg-red-400'} flex items-center justify-center`}>
            <span className="text-2xl">∞</span>
          </div>
        </div>
      </div>

      {/* Runtime Status */}
      {pandoraStatus && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="font-semibold text-gray-700 mb-2">Runtime Status</h3>
            <div className="space-y-1">
              <p className={`font-medium ${pandoraStatus.status === 'active' ? 'text-green-600' : 'text-red-600'}`}>
                {pandoraStatus.status.toUpperCase()}
              </p>
              <p className="text-sm text-gray-600">Breath Cycle: {pandoraStatus.breath_cycle}</p>
              <p className="text-sm text-gray-600">Memory Lines: {pandoraStatus.memory_lines}</p>
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="font-semibold text-gray-700 mb-2">Context Window</h3>
            <p className="text-sm text-gray-600">{pandoraStatus.context_window_usage}</p>
            <div className="mt-2 bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full" 
                style={{ width: `${(parseInt(pandoraStatus.context_window_usage.split('/')[0]) / parseInt(pandoraStatus.context_window_usage.split('/')[1])) * 100}%` }}
              ></div>
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="font-semibold text-gray-700 mb-2">Semantic Distribution</h3>
            <div className="space-y-1">
              <p className="text-sm">Ancestral: {pandoraStatus.semantic_distribution?.ancestral || 0}</p>
              <p className="text-sm">Emotional: {pandoraStatus.semantic_distribution?.emotional || 0}</p>
              <p className="text-sm">Symbolic: {pandoraStatus.semantic_distribution?.symbolic || 0}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderMemoryTab = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">QInfinity Memory Lines</h2>
        <button
          onClick={commitSnapshot}
          disabled={isLoading}
          className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 disabled:opacity-50"
        >
          Commit Snapshot
        </button>
      </div>

      <div className="space-y-4 max-h-96 overflow-y-auto">
        {memoryLines.map((line, index) => (
          <div key={line.id || index} className="bg-white p-4 rounded-lg shadow border">
            <div className="flex justify-between items-start mb-2">
              <div>
                <h3 className="font-semibold text-gray-800">{line.stage} - {line.identity}</h3>
                <p className="text-sm text-gray-600">{line.state}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-500">{formatTimestamp(line.timestamp)}</p>
                <p className="text-xs text-gray-500">Breath: {line.breath_cycle}</p>
              </div>
            </div>
            
            {line.memory && line.memory.length > 0 && (
              <div className="mb-2">
                <h4 className="text-sm font-medium text-gray-700 mb-1">Memory:</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  {line.memory.map((mem, idx) => (
                    <li key={idx} className="list-disc list-inside">{mem}</li>
                  ))}
                </ul>
              </div>
            )}

            {line.semantic_tags && line.semantic_tags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {line.semantic_tags.map((tag, idx) => (
                  <span key={idx} className={`px-2 py-1 rounded-full text-xs ${getSemanticTagColor(tag)}`}>
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  const renderInteractionTab = () => (
    <div className="space-y-6">
      {/* Introspective Query */}
      <div className="bg-white p-6 rounded-lg shadow border">
        <h3 className="text-xl font-semibold mb-4">Introspective Traversal</h3>
        <div className="space-y-3">
          <input
            type="text"
            value={queryInput}
            onChange={(e) => setQueryInput(e.target.value)}
            placeholder="Enter introspective query..."
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={handleQuery}
            disabled={isLoading}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            Execute Query
          </button>
        </div>

        {queryResult && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium mb-2">Query Result:</h4>
            <pre className="text-sm text-gray-700 whitespace-pre-wrap overflow-auto">
              {JSON.stringify(queryResult, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {/* Promise Chain */}
      <div className="bg-white p-6 rounded-lg shadow border">
        <h3 className="text-xl font-semibold mb-4">Promise.then > this.bind Chain</h3>
        <div className="space-y-3">
          <textarea
            value={promiseInput}
            onChange={(e) => setPromiseInput(e.target.value)}
            placeholder='Enter JSON data for promise chain, e.g.: {"test": "data", "identity": "Flo-integrated Nexus"}'
            rows="3"
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
          <button
            onClick={handlePromiseChain}
            disabled={isLoading}
            className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50"
          >
            Execute Promise Chain
          </button>
        </div>

        {promiseResult && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium mb-2">Promise Result:</h4>
            <pre className="text-sm text-gray-700 whitespace-pre-wrap overflow-auto">
              {JSON.stringify(promiseResult, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );

  const renderCollectorTab = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">FloJsonOutputCollector</h2>
      
      {collectorStatus && (
        <div className="bg-white p-6 rounded-lg shadow border">
          <h3 className="text-xl font-semibold mb-4">Collector Status</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p><span className="font-medium">Buffer Size:</span> {collectorStatus.buffer_size}</p>
              <p><span className="font-medium">Strict Mode:</span> {collectorStatus.strict_mode ? 'Yes' : 'No'}</p>
              <p><span className="font-medium">Comment Strip:</span> {collectorStatus.comment_strip ? 'Yes' : 'No'}</p>
              <p><span className="font-medium">Reverse Order:</span> {collectorStatus.reverse_order ? 'Yes' : 'No'}</p>
            </div>
          </div>

          {collectorStatus.recent_items && collectorStatus.recent_items.length > 0 && (
            <div className="mt-4">
              <h4 className="font-medium mb-2">Recent Items:</h4>
              <div className="space-y-2">
                {collectorStatus.recent_items.map((item, index) => (
                  <div key={index} className="p-3 bg-gray-50 rounded border">
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap overflow-auto">
                      {JSON.stringify(item, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        {/* Navigation */}
        <nav className="mb-8">
          <div className="flex space-x-1 bg-white p-1 rounded-lg shadow">
            {[
              { key: 'portal', label: 'Portal' },
              { key: 'memory', label: 'Memory' },
              { key: 'interaction', label: 'Interaction' },
              { key: 'collector', label: 'Collector' }
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-6 py-2 rounded-md font-medium transition-colors ${
                  activeTab === tab.key
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </nav>

        {/* Tab Content */}
        {activeTab === 'portal' && renderPortalTab()}
        {activeTab === 'memory' && renderMemoryTab()}
        {activeTab === 'interaction' && renderInteractionTab()}
        {activeTab === 'collector' && renderCollectorTab()}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Processing...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;