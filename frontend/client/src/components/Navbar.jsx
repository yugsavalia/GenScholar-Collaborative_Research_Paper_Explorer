import { Link } from 'wouter';
import logo from '../assets/Genscholar_logo.png';
import { useAuth } from '../context/AuthContext';
import NotificationBell from './NotificationBell';
import { useTheme } from '../hooks/useTheme';

export default function Navbar() {
  const { isAuthenticated } = useAuth();
  const { theme, toggle } = useTheme();

  return (
    <nav className="px-6 py-3" style={{ background: 'var(--panel-color)', borderBottom: '1px solid var(--border-color)' }}>
      <div className="max-w-[1400px] mx-auto flex justify-between items-center">
        <Link to="/" className="logo" data-testid="link-home">
          <img src={logo} alt="GenScholar Logo" className="logo-img" />
          <span className="logo-text">GenScholar</span>
        </Link>
        
        {isAuthenticated && (
          <div className="flex items-center gap-6">
            <button
              id="theme-toggle-btn"
              className="theme-toggle-btn"
              onClick={toggle}
              aria-label="Toggle theme"
            >
              {theme === 'light' ? '🌙' : '☀️'}
            </button>
            <Link 
              to="/dashboard" 
              className="transition-colors"
              style={{ color: 'var(--text-color)' }}
              onMouseEnter={(e) => e.target.style.color = 'var(--accent-color)'}
              onMouseLeave={(e) => e.target.style.color = 'var(--text-color)'}
              data-testid="link-dashboard"
            >
              Dashboard
            </Link>
            <Link 
              to="/profile" 
              className="transition-colors"
              style={{ color: 'var(--text-color)' }}
              onMouseEnter={(e) => e.target.style.color = 'var(--accent-color)'}
              onMouseLeave={(e) => e.target.style.color = 'var(--text-color)'}
              data-testid="link-profile"
            >
              Profile
            </Link>
            <Link 
              to="/contact" 
              className="transition-colors"
              style={{ color: 'var(--text-color)' }}
              onMouseEnter={(e) => e.target.style.color = 'var(--accent-color)'}
              onMouseLeave={(e) => e.target.style.color = 'var(--text-color)'}
              data-testid="link-contact"
            >
              Contact
            </Link>
            <NotificationBell />
            <Link 
              to="/logout" 
              className="transition-colors"
              style={{ color: 'var(--text-color)' }}
              onMouseEnter={(e) => e.target.style.color = 'var(--accent-color)'}
              onMouseLeave={(e) => e.target.style.color = 'var(--text-color)'}
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
