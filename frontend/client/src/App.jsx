import { Route, Switch, Redirect } from 'wouter';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AppProvider } from './context/AppContext';
import { useEffect } from 'react';
import { initializeSeedData } from './mocks/seed';

import Landing from './routes/Landing';
import Auth from './routes/Auth';
import Dashboard from './routes/Dashboard';
import Workspace from './routes/Workspace';
import Contact from './routes/Contact';
import Logout from './routes/Logout';

function ProtectedRoute({ component: Component, ...rest }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-[#121212] flex items-center justify-center">
        <p className="text-[#E0E0E0]">Loading...</p>
      </div>
    );
  }

  return isAuthenticated ? <Component {...rest} /> : <Redirect to="/auth" />;
}

function AppRoutes() {
  useEffect(() => {
    document.documentElement.classList.add('dark');
    
    // Only initialize seed data if backend API is not being used
    const USE_BACKEND_API = import.meta.env.VITE_USE_BACKEND_API === 'true';
    if (!USE_BACKEND_API) {
      initializeSeedData();
    }
  }, []);

  return (
    <Switch>
      <Route path="/" component={Landing} />
      <Route path="/auth" component={Auth} />
      <Route path="/contact" component={Contact} />
      <Route path="/logout" component={Logout} />
      <Route path="/dashboard">
        {() => <ProtectedRoute component={Dashboard} />}
      </Route>
      <Route path="/workspace/:id">
        {(params) => <ProtectedRoute component={Workspace} {...params} />}
      </Route>
      <Route>
        <div className="min-h-screen bg-[#121212] flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-[#E0E0E0] mb-4">404</h1>
            <p className="text-[#BDBDBD]">Page not found</p>
          </div>
        </div>
      </Route>
    </Switch>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppProvider>
        <AppRoutes />
      </AppProvider>
    </AuthProvider>
  );
}
