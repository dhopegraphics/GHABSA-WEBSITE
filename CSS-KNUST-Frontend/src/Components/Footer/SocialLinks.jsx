import React from 'react';
import { Twitter, Linkedin, Instagram } from 'lucide-react';
import { Telegram } from '@mui/icons-material';
import { SOCIAL } from '../../config/brand';

export function SocialLinks() {
  return (
    <div className="flex space-x-6">

      <a
        href={SOCIAL.twitter}
        className="text-gray-400 hover:text-blue-600"
      >
        <Twitter className="w-6 h-6" />
      </a>
      <a
        href={SOCIAL.linkedin}
        className="text-gray-400 hover:text-blue-600"
      >
        <Linkedin className="w-6 h-6" />
      </a>
      <a
        href={SOCIAL.instagram}
        className="text-gray-400 hover:text-blue-600"
      >
        <Instagram className="w-6 h-6" />
      </a>

      <a
        href={SOCIAL.telegram}
        className="text-gray-400 hover:text-blue-600"
      >
        <Telegram className="w-8 h-8" />
      </a>
    </div>
  );
}
