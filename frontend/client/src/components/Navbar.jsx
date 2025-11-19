import { Link, useLocation } from 'wouter';
import logo from '../assets/logo.jpg';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { isAuthenticated } = useAuth();
  const [location] = useLocation();
  const hideLogoText =
    location && (location.startsWith('/dashboard') || location.startsWith('/workspace'));

  return (
    <nav className="bg-[#1E1E1E] border-b border-[#2A2A2A] px-6 py-3">
      <div className="max-w-[1400px] mx-auto flex justify-between items-center">
        <Link to="/" className="logo" data-testid="link-home">
          <img src={logo} alt="GenScholar Logo" className="logo-img" />
          {!hideLogoText && <span className="logo-text">GenScholar</span>}
        </Link>
        
        {isAuthenticated && (
          <div className="flex gap-6">
            <Link 
              to="/dashboard" 
              className="text-[#E0E0E0] hover:text-[#4FC3F7] transition-colors"
              data-testid="link-dashboard"
            >
              Dashboard
            </Link>
            <Link 
              to="/contact" 
              className="text-[#E0E0E0] hover:text-[#4FC3F7] transition-colors"
              data-testid="link-contact"
            >
              Contact
            </Link>
            <Link 
              to="/logout" 
              className="text-[#E0E0E0] hover:text-[#4FC3F7] transition-colors"
              data-testid="link-logout"
            >
              Logout
            </Link>
          </div>
        )}
      </div>
    </nav>
  );
}
