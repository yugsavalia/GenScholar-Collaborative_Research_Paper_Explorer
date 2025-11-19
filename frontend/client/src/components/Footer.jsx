import { Instagram } from 'lucide-react';
import { FaXTwitter } from 'react-icons/fa6';

export default function Footer() {
  return (
    <footer className="bg-[#121212] py-8 px-4">
      <div className="max-w-[1200px] mx-auto">
        {/* Social Icons */}
        <div className="flex items-center justify-center gap-6 mb-4">
          <a 
            href="https://instagram.com" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-[#BDBDBD] hover:text-[#4FC3F7] transition-colors"
            data-testid="link-instagram"
          >
            <Instagram className="w-6 h-6" />
          </a>
          <a 
            href="https://twitter.com" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-[#BDBDBD] hover:text-[#4FC3F7] transition-colors"
            data-testid="link-twitter"
          >
            <FaXTwitter className="w-6 h-6" />
          </a>
        </div>
        
        {/* Copyright */}
        <p className="text-center text-[#BDBDBD] text-sm">
          © 2025 GenScholar. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
