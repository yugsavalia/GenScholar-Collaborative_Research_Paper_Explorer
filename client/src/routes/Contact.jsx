import Navbar from '../components/Navbar';
import instagramIcon from '../assets/icons/instagram.svg';
import twitterIcon from '../assets/icons/twitter.svg';

export default function Contact() {
  return (
    <div className="min-h-screen bg-[#121212] flex flex-col">
      <Navbar />
      
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="max-w-[600px] w-full text-center">
          <h1 className="text-3xl font-bold text-[#E0E0E0] mb-8">Contact Us</h1>
          
          <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-8">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-[#E0E0E0] mb-2">Email</h2>
              <a 
                href="mailto:contact@genscholar.com" 
                className="text-[#4FC3F7] hover:text-[#3BA7D1]"
                data-testid="link-email"
              >
                contact@genscholar.com
              </a>
            </div>

            <div className="mb-6">
              <h2 className="text-xl font-semibold text-[#E0E0E0] mb-4">Social Media</h2>
              <div className="flex items-center justify-center gap-6">
                <a 
                  href="https://instagram.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex flex-col items-center gap-2 text-[#4FC3F7] hover:text-[#3BA7D1]"
                  data-testid="link-instagram"
                >
                  <img src={instagramIcon} alt="Instagram" className="w-8 h-8" />
                  <span className="text-sm">Instagram</span>
                </a>
                <a 
                  href="https://twitter.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex flex-col items-center gap-2 text-[#4FC3F7] hover:text-[#3BA7D1]"
                  data-testid="link-twitter"
                >
                  <img src={twitterIcon} alt="Twitter" className="w-8 h-8" />
                  <span className="text-sm">Twitter</span>
                </a>
              </div>
            </div>

            <div>
              <h2 className="text-xl font-semibold text-[#E0E0E0] mb-2">Support</h2>
              <p className="text-[#BDBDBD]">
                For technical support or questions about using GenScholar, 
                please reach out via email or social media.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
