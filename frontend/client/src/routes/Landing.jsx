import { useLocation } from 'wouter';
import logo from '../assets/Genscholar_logo.png';
import Footer from '../components/Footer';
import Button from '../components/Button';

export default function Landing() {
  const [, setLocation] = useLocation();

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg-color)' }}>
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="max-w-[600px] w-full text-center">
          <img 
            src={logo} 
            alt="GenScholar Logo" 
            className="landing-logo mx-auto" 
          />
          
          <h1 className="text-4xl md:text-5xl font-bold mb-4" style={{ color: 'var(--text-color)' }}>
            GenScholar
          </h1>
          
          <p className="text-xl mb-8" style={{ color: 'var(--muted-text)' }}>
            Collaborative Research Explorer
          </p>
          
          <p className="mb-12 leading-relaxed" style={{ color: 'var(--muted-text)' }}>
            Streamline your research workflow with collaborative PDF annotation, 
            threaded discussions, and AI-powered insights. Work together on research 
            papers in real-time with your team.
          </p>
          
          <div className="flex gap-4 justify-center flex-wrap">
            <Button
              onClick={() => setLocation('/auth?tab=create')}
              variant="primary"
              data-testid="button-get-started"
            >
              Get Started
            </Button>
          </div>
        </div>
      </div>
      
      <Footer />
    </div>
  );
}
