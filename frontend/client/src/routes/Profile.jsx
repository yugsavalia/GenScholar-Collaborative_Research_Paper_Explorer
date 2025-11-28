import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getProfile } from '../api/profile';
import { formatDateTime } from '../utils/dateFormat';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Profile() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        setLoading(true);
        setError(null);
        const profileData = await getProfile();
        setProfile(profileData);
      } catch (err) {
        console.error('Failed to load profile:', err);
        setError(err.message || 'Failed to load profile');
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  // Get initials for avatar
  const getInitials = (username, firstName, lastName) => {
    if (firstName && lastName) {
      return `${firstName[0]}${lastName[0]}`.toUpperCase();
    }
    if (firstName) {
      return firstName[0].toUpperCase();
    }
    if (username) {
      return username.substring(0, 2).toUpperCase();
    }
    return 'U';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg-color)' }}>
        <Navbar />
        <div className="flex-1 flex items-center justify-center">
          <p style={{ color: 'var(--text-color)' }}>Loading profile...</p>
        </div>
        <Footer />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg-color)' }}>
        <Navbar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <p className="text-red-500 mb-4">Error: {error}</p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 rounded-md"
              style={{ background: 'var(--accent-color)', color: '#fff' }}
              onMouseEnter={(e) => e.target.style.opacity = '0.9'}
              onMouseLeave={(e) => e.target.style.opacity = '1'}
            >
              Retry
            </button>
          </div>
        </div>
        <Footer />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg-color)' }}>
        <Navbar />
        <div className="flex-1 flex items-center justify-center">
          <p style={{ color: 'var(--muted-text)' }}>No profile data available</p>
        </div>
        <Footer />
      </div>
    );
  }

  const fullName = profile.first_name || profile.last_name
    ? `${profile.first_name || ''} ${profile.last_name || ''}`.trim()
    : null;

  const initials = getInitials(profile.username, profile.first_name, profile.last_name);

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg-color)' }}>
      <Navbar />
      
      <div className="flex-1 max-w-[1400px] w-full mx-auto px-6 py-8">
        <h1 className="text-3xl font-bold mb-8" style={{ color: 'var(--text-color)' }}>My Profile</h1>

        {/* Profile Card */}
        <div className="rounded-lg p-6 mb-6" style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)' }}>
          <div className="flex items-start gap-6">
            {/* Avatar Circle */}
            <div className="w-24 h-24 rounded-full flex items-center justify-center text-white text-2xl font-bold flex-shrink-0" style={{ background: 'var(--accent-color)' }}>
              {initials}
            </div>

            {/* User Info */}
            <div className="flex-1">
              <h2 className="text-2xl font-bold mb-2" style={{ color: 'var(--text-color)' }}>
                {fullName || profile.username}
              </h2>
              {fullName && (
                <p className="mb-4" style={{ color: 'var(--muted-text)' }}>@{profile.username}</p>
              )}
              
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm" style={{ color: 'var(--muted-text)' }}>Email:</span>
                  <span className="text-sm" style={{ color: 'var(--text-color)' }}>{profile.email}</span>
                </div>
                
                {profile.date_joined && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm" style={{ color: 'var(--muted-text)' }}>Joined:</span>
                    <span className="text-sm" style={{ color: 'var(--text-color)' }}>
                      {formatDateTime(profile.date_joined)}
                    </span>
                  </div>
                )}
                
                {profile.last_login && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm" style={{ color: 'var(--muted-text)' }}>Last login:</span>
                    <span className="text-sm" style={{ color: 'var(--text-color)' }}>
                      {formatDateTime(profile.last_login)}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Stats Section */}
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-4" style={{ color: 'var(--text-color)' }}>Activity Stats</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Messages Stat */}
            <div className="rounded-lg p-6" style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)' }}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm mb-1" style={{ color: 'var(--muted-text)' }}>Total Messages</p>
                  <p className="text-3xl font-bold" style={{ color: 'var(--accent-color)' }}>
                    {profile.stats?.total_messages || 0}
                  </p>
                </div>
                <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ background: 'var(--accent-color)', opacity: 0.2 }}>
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    strokeWidth="2"
                    style={{ stroke: 'var(--accent-color)' }}
                  >
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                  </svg>
                </div>
              </div>
            </div>

            {/* PDFs Stat */}
            <div className="rounded-lg p-6" style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)' }}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm mb-1" style={{ color: 'var(--muted-text)' }}>PDFs Uploaded</p>
                  <p className="text-3xl font-bold" style={{ color: 'var(--accent-color)' }}>
                    {profile.stats?.total_pdfs_uploaded || 0}
                  </p>
                </div>
                <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ background: 'var(--accent-color)', opacity: 0.2 }}>
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    strokeWidth="2"
                    style={{ stroke: 'var(--accent-color)' }}
                  >
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                    <line x1="16" y1="13" x2="8" y2="13" />
                    <line x1="16" y1="17" x2="8" y2="17" />
                    <polyline points="10 9 9 9 8 9" />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}

