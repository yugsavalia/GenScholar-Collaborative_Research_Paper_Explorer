import { useLocation } from 'wouter';
import logo from '../assets/logo.jpg';
import Footer from '../components/Footer';
import Button from '../components/Button';

export default function Landing() {
  const [, setLocation] = useLocation();

  return (
    <div className="min-h-screen bg-[#121212] flex flex-col">
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="max-w-[600px] w-full text-center">
          <img 
            src={logo} 
            alt="GenScholar Logo" 
            className="landing-logo mx-auto" 
          />
          
          <h1 className="text-4xl md:text-5xl font-bold text-[#E0E0E0] mb-4">
            GenScholar
          </h1>
          
          <p className="text-xl text-[#BDBDBD] mb-8">
            Collaborative Research Explorer
          </p>
          
          <p className="text-[#BDBDBD] mb-12 leading-relaxed">
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
            <Button
              onClick={() => setLocation('/auth?tab=login')}
              variant="secondary"
              data-testid="button-login"
            >
              Login
            </Button>
          </div>
        </div>
      </div>
      
      <Footer />
    </div>
  );
}
