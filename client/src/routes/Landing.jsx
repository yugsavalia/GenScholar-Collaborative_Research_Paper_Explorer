import { useLocation } from 'wouter';
import { FileText, Pen, Users } from 'lucide-react';
import Footer from '../components/Footer';
import Button from '../components/Button';

export default function Landing() {
  const [, setLocation] = useLocation();

  const features = [
    {
      icon: FileText,
      title: 'Upload & Organize',
      description: 'Upload your research PDFs and organize them into workspaces for easy access and management.'
    },
    {
      icon: Pen,
      title: 'Annotate',
      description: 'Highlight, underline, and add text boxes to PDFs with powerful annotation tools.'
    },
    {
      icon: Users,
      title: 'Collaborate',
      description: 'Work together with colleagues in shared workspaces and discuss research findings.'
    }
  ];

  return (
    <div className="min-h-screen bg-[#121212] flex flex-col">
      {/* Hero Section */}
      <div className="flex-1 flex items-center justify-center px-4 py-20">
        <div className="max-w-[900px] w-full text-center">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6">
            Collaborate on Research PDFs
          </h1>
          
          <p className="text-lg md:text-xl text-[#BDBDBD] mb-12 max-w-[700px] mx-auto leading-relaxed">
            GenScholar is the ultimate platform for researchers to upload, 
            annotate, and collaborate on PDF documents with a beautiful dark 
            theme optimized for extended reading.
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
              data-testid="button-learn-more"
            >
              Learn More
            </Button>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="px-4 py-16 bg-[#0A0A0A]">
        <div className="max-w-[1200px] mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-12">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div 
                  key={index}
                  className="text-center"
                  data-testid={`feature-${feature.title.toLowerCase().replace(/\s+/g, '-')}`}
                >
                  <div className="flex justify-center mb-4">
                    <Icon className="w-12 h-12 text-[#4FC3F7]" strokeWidth={1.5} />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-3">
                    {feature.title}
                  </h3>
                  <p className="text-[#BDBDBD] leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
      
      <Footer />
    </div>
  );
}
