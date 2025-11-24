import Navbar from '../components/Navbar';

export default function Contact() {
  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg-color)' }}>
      <Navbar />
      
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="max-w-[600px] w-full text-center">
          <h1 className="text-3xl font-bold mb-8" style={{ color: 'var(--text-color)' }}>Contact Us</h1>
          
          <div className="rounded-lg p-8" style={{ background: 'var(--panel-color)', border: '1px solid var(--border-color)' }}>
            <div className="contact-section mb-5">
              <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-color)' }}>Email</h3>
              <p>
                <a 
                  href="mailto:genscholar.help@gmail.com" 
                  className="transition-colors"
                  style={{ color: 'var(--accent-color)' }}
                  onMouseEnter={(e) => e.target.style.opacity = '0.8'}
                  onMouseLeave={(e) => e.target.style.opacity = '1'}
                  data-testid="link-email"
                >
                  genscholar.help@gmail.com
                </a>
              </p>
            </div>

            <div className="contact-section mb-5">
              <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-color)' }}>Support & Help</h3>
              <p style={{ color: 'var(--muted-text)', textAlign: 'left' }}>
                If you have issues with login, workspace collaboration, PDF uploads, annotation tools, or account management, feel free to reach out anytime. Our team will guide you through any problem.
              </p>
              <p style={{ color: 'var(--muted-text)', textAlign: 'left', marginTop: '8px' }}>
                <strong style={{ color: 'var(--text-color)' }}>Response Time:</strong> Usually within 24–48 hours.
              </p>
            </div>

            <div className="contact-section">
              <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-color)' }}>Common Help Topics</h3>
              <ul style={{ color: 'var(--muted-text)', textAlign: 'left', paddingLeft: '20px' }}>
                <li>Workspace creation, roles, and permissions</li>
                <li>Uploading and managing PDFs</li>
                <li>Chat or annotation issues</li>
                <li>Account verification & login problems</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
