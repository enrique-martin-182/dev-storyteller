import './App.css';
import Header from './Header';
import RepoSubmissionForm from './RepoSubmissionForm';
import MessageDisplay from './MessageDisplay';
import RepositoryList from './RepositoryList';
import AnalysisResults from './AnalysisResults';
import { useAppContext } from '../contexts/AppContext';

function App() {
  const { isLoading } = useAppContext();

  return (
    <div className="App">
      <header className="App-header">
        <Header />
        <RepoSubmissionForm />
        <MessageDisplay />
        {isLoading && <p className="loading-indicator">Loading...</p>}
        <RepositoryList />
        <AnalysisResults />
      </header>
    </div>
  );
}

export default App;