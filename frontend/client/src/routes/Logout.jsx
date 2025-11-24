import { useEffect } from 'react';
import { useLocation } from 'wouter';
import { useAuth } from '../context/AuthContext';

export default function Logout() {
  const [, setLocation] = useLocation();
  const { logout } = useAuth();

  useEffect(() => {
    const handleLogout = async () => {
      try {
        await logout();
      } catch (error) {
        console.error('Error during logout:', error);
      } finally {
        setLocation('/');
      }
    };

    handleLogout();
  }, [logout, setLocation]);

  return (
    <div className="min-h-screen bg-[#121212] flex items-center justify-center">
      <p className="text-[#E0E0E0]">Logging out...</p>
    </div>
  );
}
