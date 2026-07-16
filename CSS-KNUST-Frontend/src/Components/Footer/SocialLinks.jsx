import React from 'react';
import { Twitter, Linkedin, Instagram } from 'lucide-react';
import { Telegram } from '@mui/icons-material';

export function SocialLinks() {
  return (
    <div className="flex space-x-6">
      
      <a
        href="https://x.com/thecssknust"
        className="text-gray-400 hover:text-blue-600"
      >
        <Twitter className="w-6 h-6" />
      </a>
      <a
        href="https://linkedin.com/in/thecssknust-original"
        className="text-gray-400 hover:text-blue-600"
      >
        <Linkedin className="w-6 h-6" />
      </a>
      <a
        href="https://instagram.com/thecssknust"
        className="text-gray-400 hover:text-blue-600"
      >
        <Instagram className="w-6 h-6" />
      </a>

      <a
        href="https://t.me/thecssknust"
        className="text-gray-400 hover:text-blue-600"
      >
        <Telegram className="w-8 h-8" />
      </a>
    </div>
  );
}
