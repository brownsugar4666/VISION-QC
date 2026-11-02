import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Inspect from './pages/Inspect';
import ReviewQueue from './pages/ReviewQueue';
import Batches from './pages/Batches';
import Reports from './pages/Reports';
import Billing from './pages/Billing';
import Journey from './pages/Journey';
import Validation from './pages/Validation';
import Models from './pages/Models';
import PlantSetup from './pages/PlantSetup';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="flex items-center justify-center min-h-screen text-gray-500">Loading...</div>;
  if (!user) return <Navigate to="/login" />;
  return children;
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<Dashboard />} />
            <Route path="inspect" element={<Inspect />} />
            <Route path="review" element={<ReviewQueue />} />
            <Route path="batches" element={<Batches />} />
            <Route path="reports" element={<Reports />} />
            <Route path="billing" element={<Billing />} />
            <Route path="journey" element={<Journey />} />
            <Route path="validation" element={<Validation />} />
            <Route path="models" element={<Models />} />
            <Route path="plants" element={<PlantSetup />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
