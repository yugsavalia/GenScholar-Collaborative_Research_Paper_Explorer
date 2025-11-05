import { useEffect } from 'react';
import { useNavigate } from 'wouter';
import { useAuth } from '../context/AuthContext';

export default function Logout() {
  const [, navigate] = useNavigate();
  const { logout } = useAuth();

  useEffect(() => {
    logout();
    navigate('/');
  }, [logout, navigate]);

  return (
    <div className="min-h-screen bg-[#121212] flex items-center justify-center">
      <p className="text-[#E0E0E0]">Logging out...</p>
    </div>
  );
}
