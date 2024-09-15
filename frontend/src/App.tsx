import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import ChatWidget from '@/components/chat-widget';
import LoginPage from '@/components/Login';
import RegisterPage from '@/components/Register';
import './styles/global.css'
import { ErrorBoundary } from '@/components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/chat" element={<ChatWidget />} />
            <Route path="/" element={<Navigate to="/chat" replace />} />
          </Routes>
        </div>
      </Router>
    </ErrorBoundary>
  );
}

export default App;