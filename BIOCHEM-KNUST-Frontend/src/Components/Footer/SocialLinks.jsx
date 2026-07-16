import { Twitter, Linkedin, Instagram } from 'lucide-react';
import { Telegram } from '@mui/icons-material';
import { SOCIAL } from '../../config/brand';

export function SocialLinks() {
  return (
    <div className="flex gap-2.5" aria-label="Social media links">

      <a
        href={SOCIAL.twitter}
        target="_blank"
        rel="noreferrer"
        aria-label="Follow us on X"
        className="flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/5 text-slate-400 hover:border-blue-300/50 hover:bg-blue-500/15 hover:text-blue-200"
      >
        <Twitter className="h-4.5 w-4.5" />
      </a>
      <a
        href={SOCIAL.linkedin}
        target="_blank"
        rel="noreferrer"
        aria-label="Follow us on LinkedIn"
        className="flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/5 text-slate-400 hover:border-blue-300/50 hover:bg-blue-500/15 hover:text-blue-200"
      >
        <Linkedin className="h-4.5 w-4.5" />
      </a>
      <a
        href={SOCIAL.instagram}
        target="_blank"
        rel="noreferrer"
        aria-label="Follow us on Instagram"
        className="flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/5 text-slate-400 hover:border-blue-300/50 hover:bg-blue-500/15 hover:text-blue-200"
      >
        <Instagram className="h-4.5 w-4.5" />
      </a>

      <a
        href={SOCIAL.telegram}
        target="_blank"
        rel="noreferrer"
        aria-label="Join us on Telegram"
        className="flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/5 text-slate-400 hover:border-blue-300/50 hover:bg-blue-500/15 hover:text-blue-200"
      >
        <Telegram sx={{ fontSize: 19 }} />
      </a>
    </div>
  );
}
