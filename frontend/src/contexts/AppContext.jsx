import { createContext, useContext, useState, useEffect } from 'react';

const AppContext = createContext();

export const useAppContext = () => {
  return useContext(AppContext);
};

const API_URL = ''; // All API calls will be relative to the current domain

// Determine WebSocket protocol based on window protocol
const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
// Construct the full WebSocket URL, relative to the current host
const WS_URL = `${wsProtocol}//${window.location.host}`;

export const AppProvider = ({ children }) => {
  const [repoUrl, setRepoUrl] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [repositories, setRepositories] = useState([]);
  const [selectedRepo, setSelectedRepo] = useState(null);
  const [analysisResults, setAnalysisResults] = useState([]);
  const [selectedForComparison, setSelectedForComparison] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchRepositories = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/v1/repositories/`);
      if (response.ok) {
        const data = await response.json();
        setRepositories(data);
      } else {
        console.error('Failed to fetch repositories:', response.statusText);
      }
    } catch (err) {
      console.error('Network error fetching repositories:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAnalysisResults = async (repoId) => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/v1/repositories/${repoId}/analysis`);
      if (response.ok) {
        const data = await response.json();
        setAnalysisResults(data);
      } else {
        console.error('Failed to fetch analysis results:', response.statusText);
        setAnalysisResults([]);
      }
    } catch (err) {
      console.error('Network error fetching analysis results:', err);
      setAnalysisResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRepositories();

    const ws = new WebSocket(`${WS_URL}/api/v1/ws/status`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setRepositories((prevRepos) =>
        prevRepos.map((repo) =>
          repo.id === data.id ? { ...repo, status: data.status } : repo
        )
      );
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    if (selectedRepo) {
      fetchAnalysisResults(selectedRepo.id);
      setSelectedForComparison([]); // Reset comparison on new repo selection
    } else {
      setAnalysisResults([]);
    }
  }, [selectedRepo]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage('');
    setError('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/v1/repositories/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: repoUrl }),
      });

      if (response.ok) {
        const data = await response.json();
        setMessage(`Analysis request submitted for: ${data.url}. Status: ${data.status}`);
        setRepoUrl('');
        fetchRepositories();
      } else {
        const errorData = await response.json();
        setError(`Error: ${errorData.detail || response.statusText}`);
      }
    } catch (err) {
      setError(`Network error: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRepoClick = (repo) => {
    setSelectedRepo(repo);
  };

  const handleComparisonSelect = (analysisId) => {
    setSelectedForComparison((prevSelected) => {
      if (prevSelected.includes(analysisId)) {
        return prevSelected.filter((id) => id !== analysisId);
      } else {
        // Limit comparison to 2 items for simplicity
        if (prevSelected.length < 2) {
          return [...prevSelected, analysisId];
        }
        return prevSelected; // Or show a message to the user
      }
    });
  };

  const value = {
    repoUrl,
    setRepoUrl,
    message,
    error,
    repositories,
    selectedRepo,
    analysisResults,
    selectedForComparison,
    isLoading,
    handleSubmit,
    handleRepoClick,
    handleComparisonSelect,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};
