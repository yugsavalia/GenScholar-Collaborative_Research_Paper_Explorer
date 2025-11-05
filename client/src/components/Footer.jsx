import instagramIcon from '../assets/icons/instagram.svg';
import twitterIcon from '../assets/icons/twitter.svg';

export default function Footer() {
  return (
    <footer className="mt-12 pt-8 border-t border-[#2A2A2A]">
      <div className="flex items-center justify-center gap-4">
        <span className="text-[#BDBDBD]">Follow us</span>
        <a 
          href="https://instagram.com" 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-[#4FC3F7] hover:text-[#3BA7D1]"
          data-testid="link-instagram"
        >
          <img src={instagramIcon} alt="Instagram" className="w-6 h-6" />
        </a>
        <a 
          href="https://twitter.com" 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-[#4FC3F7] hover:text-[#3BA7D1]"
          data-testid="link-twitter"
        >
          <img src={twitterIcon} alt="Twitter" className="w-6 h-6" />
        </a>
      </div>
    </footer>
  );
}
